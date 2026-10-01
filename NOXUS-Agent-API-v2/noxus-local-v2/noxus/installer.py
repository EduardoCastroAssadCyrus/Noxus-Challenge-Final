"""Instala scanners em Linux/WSL x86_64/arm64 via fontes oficiais HTTPS.

Instalação explícita: python -m noxus install-tools. Não executa durante import.
Dependências de SO (Java 17+, Perl, Git) são verificadas; README traz apt.
"""
import hashlib
import io
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
import httpx
from noxus.storage import atomic_json, now


def fetch(url):
    if not url.startswith('https://'):
        raise ValueError('Download exige HTTPS.')
    with httpx.Client(timeout=120, follow_redirects=True) as c:
        r = c.get(url, headers={'User-Agent':'NoxusAgent/2.0'})
        r.raise_for_status()
        return r.content

def release(repo):
    import json
    return json.loads(fetch(f'https://api.github.com/repos/{repo}/releases/latest'))

def download_asset(asset):
    data = fetch(asset['browser_download_url'])
    digest = asset.get('digest')
    if digest and digest.startswith('sha256:') and hashlib.sha256(data).hexdigest() != digest[7:]:
        raise ValueError('SHA256 divergente.')
    return data

def safe_unzip(data, destination):
    destination = Path(destination).resolve()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            target = (destination/info.filename).resolve()
            if not target.is_relative_to(destination) or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Entrada insegura no ZIP.')
        z.extractall(destination)

def install(config):
    if platform.system() != 'Linux':
        raise RuntimeError('Instalador dos scanners requer Linux/WSL. API e demonstração funcionam no Windows.')
    for required in ('java','perl','git'):
        if not shutil.which(required):
            raise RuntimeError(f'Pré-requisito ausente: {required}. Consulte README.')
    root = Path(config['agent_state_dir']).parent / 'tools'
    root.mkdir(parents=True,exist_ok=True)
    commands = config.setdefault('commands',{})
    versions = {}
    if not shutil.which('semgrep') and not commands.get('semgrep'):
        subprocess.run([sys.executable,'-m','pip','install','--index-url','https://pypi.org/simple','semgrep'],check=True)
        commands['semgrep'] = [str(Path(sys.executable).parent/'semgrep')]
    arch = {'x86_64':'x64','aarch64':'arm64'}.get(platform.machine())
    if not arch:
        raise RuntimeError('Arquitetura não suportada pelo instalador.')
    if not shutil.which('gitleaks') and not commands.get('gitleaks'):
        rel = release('gitleaks/gitleaks')
        asset = next(a for a in rel['assets'] if a['name'].endswith(f'linux_{arch}.tar.gz'))
        data = download_asset(asset)
        checks = next(a for a in rel['assets'] if 'checksums' in a['name'])
        checks_text = download_asset(checks).decode()
        expected = next(line.split()[0] for line in checks_text.splitlines() if line.split()[-1].lstrip('*') == asset['name'])
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Checksum Gitleaks inválido.')
        with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as tar:
            member = next(m for m in tar.getmembers() if m.name == 'gitleaks' and m.isfile())
            (root/'gitleaks').write_bytes(tar.extractfile(member).read())
        (root/'gitleaks').chmod(0o700)
        commands['gitleaks'] = [str(root/'gitleaks')]
        versions['gitleaks'] = rel['tag_name']
    if not shutil.which('nikto') and not commands.get('nikto'):
        path = root/'nikto'
        if not path.exists():
            subprocess.run(['git','clone','--depth','1','https://github.com/sullo/nikto.git',str(path)],check=True)
        if not (path/'program/nikto.pl').exists():
            raise RuntimeError('Instalação Nikto incompleta; revise tools/nikto.')
        commands['nikto'] = ['perl',str(path/'program/nikto.pl')]
        versions['nikto_commit'] = subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
    if not shutil.which('dependency-check.sh') and not commands.get('dependency-check'):
        rel = release('dependency-check/DependencyCheck')
        asset = next(a for a in rel['assets'] if a['name'].endswith('-release.zip'))
        safe_unzip(download_asset(asset),root)
        exe = root/'dependency-check/bin/dependency-check.sh'
        exe.chmod(0o700)
        commands['dependency-check'] = [str(exe)]
        versions['dependency-check'] = rel['tag_name']
    atomic_json(root/'installed.json',{'installed_at':now(),'versions':versions,'commands':commands})
    return config
