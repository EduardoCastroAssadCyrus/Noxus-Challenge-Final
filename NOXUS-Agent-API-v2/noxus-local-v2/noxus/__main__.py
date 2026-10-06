import argparse
import json
import logging
import os
import secrets
import subprocess
import sys
from pathlib import Path
from uuid import uuid4
from noxus.agent import NoxusAgent, TOOLS, local_repository_path
from noxus.storage import atomic_json, read_json, now
from noxus.scanner_help import show_installation_help


def main():
    parser = argparse.ArgumentParser(description='NoxusAgent + API local JSON')
    parser.add_argument('--config', default='.noxus/config.json', help='Caminho de configuração (antes do subcomando)')
    sub = parser.add_subparsers(dest='action',required=True)
    init = sub.add_parser('init',help='Configuração interativa')
    init.add_argument('--no-install-help', action='store_true', help=argparse.SUPPRESS)
    serve = sub.add_parser('serve',help='Inicia API em loopback')
    serve.add_argument('--port',type=int,default=8000)
    sub.add_parser('doctor',help='Verifica executáveis')
    sub.add_parser('install-tools',help='Instala scanners via fontes oficiais no Linux/WSL')
    scan = sub.add_parser('scan',help='Varredura única')
    scan.add_argument('--tools',nargs='+',choices=TOOLS,default=TOOLS)
    sub.add_parser('watch',help='Monitora continuamente em primeiro plano')
    sub.add_parser('start',help='Inicia monitor em segundo plano')
    sub.add_parser('flush',help='Reenvia fila pendente')
    sub.add_parser('demo',help='Envia exemplo sintético; não executa scanners')
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    if args.action == 'init':
        if config_path.exists():
            parser.error('Configuração já existe; edite o JSON ou escolha outro --config.')
        def ask(label, default=''):
            return input(label+(f' [{default}]' if default else '')+': ').strip() or default
        repo = str(local_repository_path(ask('Pasta LOCAL do repositório',str(Path.cwd()))))
        name = ask('Nome do desenvolvedor')
        role = ask('Cargo') or None
        team = ask('Equipe') or None
        repository = ask('URL HTTPS do repositório (opcional; Enter para deixar vazio)') or None
        asset_name = ask('Nome do ativo',Path(repo).name)
        target = ask('URL da aplicação local (vazio se não houver)') or None
        state = config_path.parent
        config = {'developer':{'name':name,'role':role,'team':team},
            'asset':{'id':str(uuid4()),'name':asset_name,'type':'web-api','repository_url':repository,
                'branch':'main','commit':None,'local_ip':None,'application_url':target,'consumed_apis':[]},
            'repository_path':repo,'agent_state_dir':str(state/'agent'), 'data_dir':str(state/'dados'),
            'api_url':'http://127.0.0.1:8000','api_key':secrets.token_urlsafe(32),
            'commands':{},'semgrep_config':'p/default','scan_timeout_seconds':1800,
            'poll_seconds':2,'debounce_seconds':3,'sca_interval_seconds':86400}
        agent = NoxusAgent(config)
        atomic_json(config_path,config)
        print('Configuração criada. Edite asset.consumed_apis para cadastrar APIs consumidas.')
        if not args.no_install_help:
            show_installation_help(agent, config_path, compact=True)
        return
    if not config_path.exists():
        parser.error('Execute init primeiro.')
    config = read_json(config_path)
    if args.action == 'serve':
        import uvicorn
        from noxus.api import create_app
        uvicorn.run(create_app(config['data_dir'],os.getenv('NOXUS_API_KEY') or config['api_key']),host='127.0.0.1',port=args.port)
        return
    if args.action == 'install-tools':
        from noxus.installer import install
        try:
            install(config)
        finally:
            # Preserva instalações já concluídas se uma ferramenta falhar.
            atomic_json(config_path,config)
        print('Scanners configurados. Execute doctor.')
        return
    if args.action == 'start':
        state = Path(config['agent_state_dir']); state.mkdir(parents=True,exist_ok=True)
        with open(state/'agent.log','ab') as stream:
            kwargs = {'stdout':stream,'stderr':stream,'stdin':subprocess.DEVNULL}
            if os.name == 'nt':
                kwargs['creationflags'] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                kwargs['start_new_session'] = True
            child = subprocess.Popen([sys.executable,'-m','noxus','--config',str(config_path),'watch'],**kwargs)
        atomic_json(state/'process.json',{'pid':child.pid,'started_at':now()})
        print(f'Monitor iniciado com PID {child.pid}. Log: {state / "agent.log"}. Para encerrar use o gerenciador de processos ou kill PID.')
        return
    agent = NoxusAgent(config)
    if args.action in {'doctor', 'scan', 'watch'}:
        show_installation_help(agent, config_path, args.tools if args.action == 'scan' else None)
    if args.action == 'doctor':
        print(json.dumps(agent.doctor(),indent=2))
    elif args.action == 'scan':
        results = agent.scan(args.tools)
        if any(r['scan']['status'] != 'completed' for r in results):
            sys.exit(1)
    elif args.action == 'watch':
        agent.watch()
    elif args.action == 'flush':
        print(f'{agent.flush()} relatórios enviados.')
    elif args.action == 'demo':
        from noxus.models import ScanEnvelope
        doc = agent.envelope('semgrep','manual',now(),now(),'completed',[],None)
        doc['findings'] = [{'title':'DEMONSTRAÇÃO: SQL Injection fictícia','description':'Exemplo sintético, não é resultado de scanner.',
            'rule_id':'demo.sql-injection','severity':'high','cwe':['CWE-89'],'location':{'file':'demo.py','line':10}}]
        doc = ScanEnvelope.model_validate(doc).model_dump(mode='json')
        atomic_json(agent.pending/(doc['scan']['id']+'.json'),doc)
        print(f'Demonstração: {agent.flush()} relatório enviado; confira /docs.')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nNoxusAgent encerrado.')
    except (ValueError, RuntimeError, TimeoutError) as e:
        print(f'Erro: {e}',file=sys.stderr)
        sys.exit(1)
