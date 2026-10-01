import io
import zipfile
import pytest
from noxus.agent import NoxusAgent
from noxus.installer import safe_unzip


def test_watch_changes_commit_dependencies_and_online(config,monkeypatch):
    a=NoxusAgent(config)
    snapshots=iter([('a','a','a'),('b','b','b'),('b','b','b')])
    monkeypatch.setattr(a,'snapshot',lambda:next(snapshots))
    config['debounce_seconds']=0
    calls=[]
    monkeypatch.setattr(a,'run_scan',lambda tool,trigger:calls.append((tool,trigger)))
    monkeypatch.setattr(a,'flush',lambda:None)
    monkeypatch.setattr('noxus.agent.online',lambda url:True)
    def stop(_): raise KeyboardInterrupt()
    monkeypatch.setattr('noxus.agent.time.sleep',stop)
    with pytest.raises(KeyboardInterrupt): a.watch()
    assert ('semgrep','commit') in calls
    assert ('dependency-check','dependency-change') in calls
    assert calls.count(('nikto','app-online'))==1


def test_zip_traversal_rejected(tmp_path):
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w') as z: z.writestr('../escape.txt','bad')
    with pytest.raises(ValueError): safe_unzip(buffer.getvalue(),tmp_path/'tools')
    assert not (tmp_path/'escape.txt').exists()
