import json
import sys
import httpx
import pytest
from noxus.agent import NoxusAgent, local_target
from noxus.parsers import normalize


def test_gitleaks_no_secret():
    findings,partial=normalize('gitleaks',[{'RuleID':'key','File':'.env','StartLine':1,'Secret':'SENSITIVE','Match':'SENSITIVE'}])
    assert 'SENSITIVE' not in findings[0].model_dump_json()

def test_semgrep_error_marks_partial():
    assert normalize('semgrep',{'results':[],'errors':[{'message':'bad'}]})[1] is True

def test_sca():
    findings,_=normalize('dependency-check',{'dependencies':[{'fileName':'lib.jar','vulnerabilities':[{'name':'CVE-2024-12345','severity':'HIGH'}]}]})
    assert findings[0].cve==['CVE-2024-12345']

def test_nikto():
    f,_=normalize('nikto',{'vulnerabilities':[{'id':1,'url':'/login?token=secret','msg':'Missing header'}]},'http://localhost:8080')
    assert f[0].location.url=='http://localhost:8080/login' and f[0].severity is None

@pytest.mark.parametrize('target',['https://example.com','http://192.168.1.1','http://user:password@localhost'])
def test_local_only(target):
    with pytest.raises(ValueError): local_target(target)

def test_command_prefix_not_mutated(config):
    config['commands']['semgrep']=['custom'];a=NoxusAgent(config)
    cmd=a.command_prefix('semgrep');cmd+=['scan']
    assert config['commands']['semgrep']==['custom']

def test_missing_scanner_is_failed(config):
    config['commands']['semgrep']=['/nonexistent/noxus-scanner'];a=NoxusAgent(config)
    doc=a.run_scan('semgrep')
    assert doc['scan']['status']=='failed' and not doc['findings']
    assert len(list(a.pending.glob('*.json')))==1

def test_real_subprocess_adapter(config,tmp_path):
    stub=tmp_path/'scanner.py'
    stub.write_text("import sys,json\np=sys.argv[sys.argv.index('--output')+1]\njson.dump({'results':[{'check_id':'rule','path':'app.py','start':{'line':3},'extra':{'severity':'ERROR','message':'demo'}}],'errors':[]},open(p,'w'))\n")
    config['commands']['semgrep']=[sys.executable,str(stub)]
    a=NoxusAgent(config);doc=a.run_scan('semgrep')
    assert doc['scan']['status']=='completed' and len(doc['findings'])==1

def test_queue_retry_and_send(config,monkeypatch):
    a=NoxusAgent(config);config['commands']['semgrep']=['/nonexistent/scanner'];doc=a.run_scan('semgrep')
    calls=[]
    def handler(request):
        calls.append(json.loads(request.content))
        if len(calls)==1: raise httpx.ConnectError('offline')
        return httpx.Response(200,json={'scan_id':doc['scan']['id']})
    original=httpx.Client
    monkeypatch.setattr('noxus.agent.httpx.Client',lambda **kw:original(transport=httpx.MockTransport(handler)))
    assert a.flush()==0 and list(a.pending.glob('*.json'))
    assert a.flush()==1 and not list(a.pending.glob('*.json'))
    assert calls[0]['scan']['id']==calls[1]['scan']['id']

def test_permanent_rejection_kept(config,monkeypatch):
    a=NoxusAgent(config);config['commands']['semgrep']=['/nonexistent/scanner'];a.run_scan('semgrep')
    original=httpx.Client
    monkeypatch.setattr('noxus.agent.httpx.Client',lambda **kw:original(transport=httpx.MockTransport(lambda r:httpx.Response(422))))
    assert a.flush()==0 and len(list((a.state/'rejected').glob('*.json')))==1

def test_snapshot_dependency_changes(config):
    a=NoxusAgent(config);old=a.snapshot();(a.repo/'requirements.txt').write_text('requests');new=a.snapshot()
    assert old[0]!=new[0] and old[1]!=new[1]
