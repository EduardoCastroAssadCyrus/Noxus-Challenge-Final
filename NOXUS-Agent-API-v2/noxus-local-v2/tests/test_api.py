from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from noxus.api import create_app
from noxus.models import ScanEnvelope
from noxus.storage import JsonStore


def test_ingest_replay_conflict_persistence(client,headers,payload):
    assert client.post('/api/findings',json=payload).status_code==401
    r=client.post('/api/findings',json=payload,headers=headers)
    assert r.status_code==200,r.text
    assert r.json()['replayed'] is False
    assert client.post('/api/findings',json=payload,headers=headers).json()['replayed'] is True
    payload['developer']['name']='Other'
    assert client.post('/api/findings',json=payload,headers=headers).status_code==409
    with TestClient(create_app(client.app.state.store.root,'test-key')) as restarted:
        assert restarted.get('/api/findings',headers=headers).json()['total']==1

def test_concurrent_replay(tmp_path,payload):
    doc=ScanEnvelope.model_validate(payload)
    def put(_):
        return JsonStore(tmp_path).ingest(doc)
    with ThreadPoolExecutor(max_workers=8) as pool:
        responses=list(pool.map(put,range(16)))
    assert sum(not r['replayed'] for r in responses)==1
    assert len(list((tmp_path/'scans').glob('*.json')))==1

def test_extension_route(client,headers,payload):
    route='/api/integrations/noxus-vscode/scans'
    assert client.post(route,json=payload,headers=headers).status_code==422
    payload['source']='noxus-vscode-extension'; payload['scan']['tool']='sonar'
    assert client.post(route,json=payload,headers=headers).status_code==200
    rows=client.get('/api/findings?source=noxus-vscode-extension',headers=headers).json()
    assert rows['total']==1 and rows['items'][0]['tool']=='sonar'

@pytest.mark.parametrize('tool,category',[('dependency-reputation','SCA'),('extension-reputation','EXTENSION'),('gitleaks','SECRET')])
def test_extension_other_scans(client,headers,payload,tool,category):
    payload['source']='noxus-vscode-extension'; payload['scan'].update(tool=tool,category=category)
    assert client.post('/api/integrations/noxus-vscode/scans',json=payload,headers=headers).status_code==200

@pytest.mark.parametrize('change',[{'source':'other'},{'schema_version':'2.0'},{'secret':'LEAKME'}])
def test_invalid_contract(client,headers,payload,change):
    payload.update(change)
    r=client.post('/api/findings',json=payload,headers=headers)
    assert r.status_code==422 and 'LEAKME' not in r.text

@pytest.mark.parametrize('change',[{'category':'DAST'},{'started_at':'2026-09-30T22:00:00'}, {'finished_at':'2025-09-30T22:00:00-03:00'}, {'status':'failed'}])
def test_invalid_scan(client,headers,payload,change):
    payload['scan'].update(change)
    assert client.post('/api/findings',json=payload,headers=headers).status_code==422

def test_empty_and_failure(client,headers,payload):
    payload['findings']=[]
    assert client.post('/api/findings',json=payload,headers=headers).status_code==200
    payload['scan'].update(id=str(uuid4()),status='failed',error='Scanner ausente')
    assert client.post('/api/findings',json=payload,headers=headers).status_code==200
    assert client.get('/api/dashboard',headers=headers).json()['total_scans']==2
    assert client.get('/api/findings',headers=headers).json()['total']==0

def test_triage_survives_new_scan(client,headers,payload):
    client.post('/api/findings',json=payload,headers=headers)
    key=client.get('/api/findings',headers=headers).json()['items'][0]['id']
    change={'status':'accepted_risk','actor':'Eduardo','reason':'Teste acadêmico'}
    assert client.patch(f'/api/findings/{key}/status',json=change,headers=headers).status_code==200
    payload['scan']['id']=str(uuid4());client.post('/api/findings',json=payload,headers=headers)
    item=client.get('/api/findings',headers=headers).json()['items'][0]
    assert item['status']=='accepted_risk' and item['occurrences']==2
    assert len(client.get(f'/api/findings/{key}/history',headers=headers).json()['history'])==1

def test_secret_scrub(client,headers,payload):
    payload['scan'].update(tool='gitleaks',category='SECRET')
    payload['findings'][0].update(title='SENSITIVE',description='SENSITIVE',recommendation='SENSITIVE')
    assert client.post('/api/findings',json=payload,headers=headers).status_code==200
    assert 'SENSITIVE' not in next(client.app.state.store.scans.glob('*.json')).read_text()

def test_url_credentials_rejected(client,headers,payload):
    payload['asset']['repository_url']='https://user:password@github.com/repo'
    r=client.post('/api/findings',json=payload,headers=headers)
    assert r.status_code==422 and 'password@' not in r.text

def test_body_limit(client,headers):
    assert client.post('/api/findings',content=b'x'*(10*1024*1024+1),headers=headers).status_code==413

def test_duplicate_in_same_scan(client,headers,payload):
    payload['findings']*=2;client.post('/api/findings',json=payload,headers=headers)
    assert client.get('/api/findings',headers=headers).json()['items'][0]['occurrences']==1

def test_scans_detail_schema_assets(client,headers,payload):
    client.post('/api/findings',json=payload,headers=headers)
    assert client.get('/api/scans',headers=headers).json()['total']==1
    assert client.get('/api/scans/'+payload['scan']['id'],headers=headers).status_code==200
    assert client.get('/api/scans/'+str(uuid4()),headers=headers).status_code==404
    assert client.get('/api/assets',headers=headers).json()['total']==1
    assert 'source' in client.get('/api/schema',headers=headers).json()['properties']
