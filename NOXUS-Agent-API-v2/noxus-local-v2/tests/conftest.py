import pytest
from fastapi.testclient import TestClient
from noxus.api import create_app

@pytest.fixture
def payload():
    return {'schema_version':'1.0','source':'noxus-agent','developer':{'name':'Eduardo','role':'Dev','team':'Backend'},
        'asset':{'id':'backend','name':'Backend','repository_url':'https://github.com/equipe/backend','application_url':'http://localhost:8080','consumed_apis':[]},
        'scan':{'id':'a578af66-a49a-4913-909f-3dd1af647813','tool':'semgrep','category':'SAST','started_at':'2026-09-30T22:00:00-03:00','finished_at':'2026-09-30T22:00:01-03:00','status':'completed'},
        'findings':[{'title':'Possível SQL Injection','rule_id':'sql-injection','severity':'high','location':{'file':'app.py','line':10},'cwe':['CWE-89']}]}

@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path/'data','test-key')) as c:
        yield c

@pytest.fixture
def headers():
    return {'X-API-Key':'test-key'}

@pytest.fixture
def config(tmp_path,payload):
    repo=tmp_path/'repo'; repo.mkdir()
    return {'developer':payload['developer'],'asset':payload['asset'],'repository_path':str(repo),
        'agent_state_dir':str(tmp_path/'agent'),'data_dir':str(tmp_path/'data'),
        'api_url':'http://127.0.0.1:8000','api_key':'test-key','commands':{}}
