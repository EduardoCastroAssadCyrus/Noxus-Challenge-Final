"""NoxusAgent: execução local, normalização, fila durável e monitoramento por polling."""
import copy
import hashlib
import ipaddress
import json
import logging
import os
import platform
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4
import httpx
from noxus.models import ScanEnvelope, TOOL_CATEGORIES, NOXUS_AGENT_SOURCE
from noxus.parsers import normalize
from noxus.storage import atomic_json, file_lock, now, read_json
from noxus.tool_paths import scanner_command, perl_executable, java_executable, java_environment

log = logging.getLogger('noxus-agent')
TOOLS = ['semgrep', 'gitleaks', 'dependency-check', 'nikto']
IGNORED = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', '.noxus', 'dados', 'dist', 'build', '.pytest_cache'}
MANIFESTS = {'requirements.txt', 'poetry.lock', 'uv.lock', 'Pipfile.lock', 'package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'pom.xml', 'build.gradle', 'build.gradle.kts', 'go.mod', 'go.sum', 'Cargo.lock', 'composer.lock'}

def local_repository_path(value):
    # Aceita caminhos colados com ou sem aspas, inclusive com espaços.
    value = str(value).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in (chr(34), chr(39)):
        value = value[1:-1]
    if not value:
        raise ValueError('Informe a pasta local do projeto.')
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise ValueError('Diretório local do repositório não existe.')
    return path


def git(repo, *args):
    try:
        r = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None

def local_target(url):
    if not url:
        return None
    p = urlsplit(url)
    if p.scheme not in ('http','https') or p.username or p.password or p.query or p.fragment:
        raise ValueError('Alvo Nikto deve ser uma URL local sem credenciais/query/fragmento.')
    host = p.hostname
    if host == 'localhost':
        host = '127.0.0.1'
    if not host or not ipaddress.ip_address(host).is_loopback:
        raise ValueError('Este MVP aceita Nikto somente em localhost ou IP de loopback.')
    return host, p.port or (443 if p.scheme == 'https' else 80)

def online(url):
    target = local_target(url)
    if not target:
        return False
    try:
        with socket.create_connection(target, timeout=1):
            return True
    except OSError:
        return False

def execute(command, cwd, timeout, env=None):
    """Sem shell. Descarta stdout/stderr do scanner para não registrar segredos."""
    kwargs = {'cwd': cwd, 'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL}
    if env is not None:
        kwargs['env'] = env
    if os.name != 'nt':
        kwargs['start_new_session'] = True
    proc = subprocess.Popen(command, **kwargs)
    try:
        return proc.wait(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        if os.name != 'nt':
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()
        proc.wait()
        raise

class NoxusAgent:
    def __init__(self, config):
        self.config = config
        self.repo = local_repository_path(config['repository_path'])
        self.state = Path(config['agent_state_dir']).resolve()
        self.pending = self.state / 'pending'
        self.pending.mkdir(parents=True, exist_ok=True)
        local_target(config['asset'].get('application_url'))
        # Bloqueia configuração inválida antes de executar ferramentas.
        probe = self.envelope('semgrep', 'manual', now(), now(), 'completed', [], None)
        ScanEnvelope.model_validate(probe)
        endpoint = urlsplit(config['api_url'])
        if endpoint.scheme not in ('http', 'https') or not endpoint.hostname or endpoint.username or endpoint.password:
            raise ValueError('api_url inválida.')

    def command_prefix(self, tool):
        configured = self.config.get('commands', {}).get(tool)
        if configured:
            if not isinstance(configured,list) or not all(isinstance(x,str) for x in configured):
                raise ValueError('commands deve conter listas de argumentos.')
            return list(configured)
        return scanner_command(tool, self.state)

    def doctor(self):
        result = {}
        for tool in TOOLS:
            command = self.command_prefix(tool)
            available = bool(shutil.which(command[0]))
            if tool == 'dependency-check':
                available = available and bool(java_executable())
            if tool == 'nikto':
                # Encontrar Perl não significa que o script Nikto também existe.
                # Um caminho absoluto para Perl também funciona fora do PATH.
                available = available and bool(
                    shutil.which(command[0]) if Path(command[0]).stem.lower() == 'perl'
                    else perl_executable()
                )
                for argument in command[1:]:
                    if argument.lower().endswith('.pl'):
                        available = available and (self.repo / argument).is_file()
            result[tool] = bool(available)
        return result

    def envelope(self, tool, trigger, start, end, status, findings, error):
        asset = copy.deepcopy(self.config['asset'])
        asset['branch'] = git(self.repo, 'branch', '--show-current') or asset.get('branch', 'main')
        asset['commit'] = git(self.repo, 'rev-parse', 'HEAD')
        try:
            asset['local_ip'] = socket.gethostbyname(socket.gethostname())
        except OSError:
            asset['local_ip'] = None
        return dict(schema_version='1.0', source=NOXUS_AGENT_SOURCE,
            developer=self.config['developer'], asset=asset,
            scan=dict(id=str(uuid4()), tool=tool, tool_version=None, category=TOOL_CATEGORIES[tool],
                started_at=start, finished_at=end, status=status, trigger=trigger, error=error),
            findings=[f.model_dump(mode='json') for f in findings])

    def run_scan(self, tool, trigger='manual'):
        start = now()
        findings, error, status = [], None, 'completed'
        log.info('Iniciando %s (%s)', tool, trigger)
        try:
            with tempfile.TemporaryDirectory(prefix='noxus-scan-') as tmp:
                report = Path(tmp) / 'report.json'
                cmd = self.command_prefix(tool)
                if tool == 'semgrep':
                    cmd += ['scan', '--config', self.config.get('semgrep_config','p/default'), '--metrics=off',
                            '--disable-version-check', '--json', '--output', str(report), str(self.repo)]
                elif tool == 'gitleaks':
                    cmd += ['dir', str(self.repo), '--report-format', 'json', '--report-path', str(report), '--redact=100', '--exit-code', '10', '--no-banner']
                elif tool == 'dependency-check':
                    cmd += ['--project', self.config['asset']['id'], '--scan', str(self.repo), '--format', 'JSON', '--out', tmp]
                    report = Path(tmp) / 'dependency-check-report.json'
                elif tool == 'nikto':
                    target = self.config['asset'].get('application_url')
                    if not target or not online(target):
                        raise ValueError('Aplicação local indisponível ou URL não configurada.')
                    cmd += ['-h', target, '-Format', 'json', '-output', str(report), '-ask', 'no']
                else:
                    raise ValueError('Ferramenta não suportada.')
                environment = java_environment() if tool == 'dependency-check' else None
                code = execute(cmd, str(self.repo), self.config.get('scan_timeout_seconds', 1800), env=environment)
                accepted = (0,10) if tool == 'gitleaks' else (0,)
                if code not in accepted:
                    raise ValueError(f'Ferramenta terminou com código {code}; verifique a instalação/configuração.')
                if not report.exists():
                    raise ValueError('Ferramenta não produziu relatório JSON.')
                if report.stat().st_size > 50 * 1024 * 1024:
                    raise ValueError('Relatório excedeu 50 MiB.')
                findings, partial = normalize(tool, read_json(report), self.config['asset'].get('application_url'))
                if partial:
                    status, error = 'partial', 'Scanner informou erros de análise; cobertura incompleta.'
        except FileNotFoundError:
            status, error = 'failed', 'Scanner não instalado ou comando inexistente. Execute doctor/install-tools.'
        except subprocess.TimeoutExpired:
            status, error = 'failed', 'Tempo máximo da varredura excedido.'
        except (ValueError, KeyError, TypeError, AttributeError, OSError):
            # Não incluir conteúdo bruto nem mensagens externas potencialmente sensíveis.
            status, error = 'failed', 'Execução ou relatório inválido. Verifique versão, pré-requisitos e configuração do scanner.'
        payload = ScanEnvelope.model_validate(self.envelope(tool, trigger, start, now(), status, findings, error))
        doc = payload.model_dump(mode='json')
        atomic_json(self.pending / (doc['scan']['id']+'.json'), doc)
        log.info('%s: %s; %d findings; relatório na fila', tool, status, len(findings))
        return doc

    def flush(self):
        sent = 0
        key = os.getenv('NOXUS_API_KEY') or self.config['api_key']
        with file_lock(self.state / '.queue.lock'):
            with httpx.Client(timeout=15, trust_env=False, follow_redirects=False) as client:
                for path in sorted(self.pending.glob('*.json')):
                    doc = read_json(path)
                    try:
                        r = client.post(self.config['api_url'].rstrip('/')+'/api/findings', json=doc, headers={'X-API-Key':key})
                    except httpx.TransportError:
                        log.warning('API indisponível; mantendo fila para reenvio.')
                        break
                    if r.status_code == 200 and r.json().get('scan_id') == doc['scan']['id']:
                        path.unlink(); sent += 1
                    elif r.status_code in (409,413,422):
                        dest = self.state / 'rejected' / path.name
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        os.replace(path,dest)
                        log.error('Relatório rejeitado HTTP %s; preservado em rejected.',r.status_code)
                    else:
                        log.warning('Envio HTTP %s; mantendo fila.', r.status_code)
                        break
        return sent

    def scan(self, tools=None, trigger='manual'):
        with file_lock(self.state / '.agent.lock', timeout=.2):
            result = [self.run_scan(tool,trigger) for tool in (tools or TOOLS)]
            self.flush()
            return result

    def snapshot(self):
        code, deps = hashlib.sha256(), hashlib.sha256()
        for root, dirs, files in os.walk(self.repo):
            dirs[:] = sorted(d for d in dirs if d not in IGNORED and not Path(root,d).is_symlink())
            for name in sorted(files):
                p = Path(root,name)
                if p.is_symlink():
                    continue
                try:
                    s = p.stat()
                    marker = f'{p.relative_to(self.repo)}:{s.st_mtime_ns}:{s.st_size}'.encode()
                    code.update(marker)
                    if name in MANIFESTS:
                        deps.update(marker)
                except OSError:
                    continue
        return code.hexdigest(), deps.hexdigest(), git(self.repo,'rev-parse','HEAD')

    def watch(self):
        # Não modifica hooks Git. Detecta commits por mudança de HEAD.
        with file_lock(self.state / '.agent.lock', timeout=.2):
            current = self.snapshot()
            for tool in TOOLS[:3]:
                self.run_scan(tool,'startup')
            target = self.config['asset'].get('application_url')
            was_online = False
            last_sca = time.monotonic()
            dirty_since = None
            pending = set()
            while True:
                new = self.snapshot()
                if new != current:
                    pending.update(['semgrep','gitleaks'])
                    if new[1] != current[1]:
                        pending.add('dependency-check')
                    trigger = 'commit' if new[2] != current[2] else 'file-change'
                    current, dirty_since = new, time.monotonic()
                if dirty_since is not None and time.monotonic()-dirty_since >= self.config.get('debounce_seconds',3):
                    for tool in TOOLS:
                        if tool in pending:
                            self.run_scan(tool,'dependency-change' if tool == 'dependency-check' else trigger)
                    pending.clear(); dirty_since = None
                is_online = online(target)
                if is_online and not was_online:
                    self.run_scan('nikto','app-online')
                was_online = is_online
                if time.monotonic()-last_sca >= self.config.get('sca_interval_seconds',86400):
                    self.run_scan('dependency-check','scheduled'); last_sca = time.monotonic()
                self.flush()
                time.sleep(self.config.get('poll_seconds',2))
