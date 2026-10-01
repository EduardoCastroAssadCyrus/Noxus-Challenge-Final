"""Persistência JSON. Nenhum SQL, ORM ou servidor de banco é utilizado."""
import hashlib
import json
import os
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.noxus-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)

@contextmanager
def file_lock(path, timeout=30):
    """Lock entre processos; liberado pelo SO inclusive após encerramento abrupto."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'a+b') as f:
        if f.tell() == 0:
            f.write(b'0'); f.flush()
        start = time.monotonic()
        while True:
            try:
                if os.name == 'nt':
                    import msvcrt
                    f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except (OSError, BlockingIOError):
                if time.monotonic() - start >= timeout:
                    raise TimeoutError('Outro processo está usando os arquivos.')
                time.sleep(.05)
        try:
            yield
        finally:
            if os.name == 'nt':
                f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

def fingerprint(doc, finding):
    # Mantém scanners/origens separados: correlação entre ferramentas fica para IA.
    identity = [doc['asset']['id'], doc['asset']['repository_url'], doc['asset']['branch'],
                doc['source'], doc['scan']['tool'], finding['rule_id'], finding['location'], finding['dependency']]
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()

class Conflict(ValueError):
    pass

class JsonStore:
    def __init__(self, root):
        self.root = Path(root)
        self.scans = self.root / 'scans'
        self.scans.mkdir(parents=True, exist_ok=True)
        self.lock = self.root / '.storage.lock'

    def ingest(self, envelope):
        doc = envelope.model_dump(mode='json')
        path = self.scans / (doc['scan']['id'] + '.json')
        with file_lock(self.lock):
            if path.exists():
                if read_json(path)['payload'] != doc:
                    raise Conflict('scan.id já existe com conteúdo diferente.')
                replayed = True
            else:
                atomic_json(path, {'received_at': now(), 'payload': doc})
                replayed = False
        return {'scan_id': doc['scan']['id'], 'received': len(doc['findings']), 'replayed': replayed}

    def scan_list(self):
        # Arquivos são substituídos atomicamente; leitores nunca veem escrita parcial.
        return sorted([read_json(p) for p in self.scans.glob('*.json')], key=lambda x: x['received_at'])

    def findings(self):
        aggregated = {}
        for record in self.scan_list():
            doc = record['payload']
            seen = set()
            for finding in doc['findings']:
                key = fingerprint(doc, finding)
                if key in seen:
                    continue
                seen.add(key)
                previous = aggregated.get(key)
                stamp = doc['scan']['finished_at']
                if previous:
                    previous['occurrences'] += 1
                    if datetime.fromisoformat(stamp) < datetime.fromisoformat(previous['last_seen']):
                        previous['first_seen'] = min(previous['first_seen'], stamp, key=datetime.fromisoformat)
                        continue
                aggregated[key] = {**finding, 'id': key, 'asset_id': doc['asset']['id'],
                    'source': doc['source'], 'tool': doc['scan']['tool'], 'category': doc['scan']['category'],
                    'developer': doc['developer'], 'branch': doc['asset']['branch'],
                    'first_seen': previous['first_seen'] if previous else stamp,
                    'last_seen': stamp, 'last_scan_id': doc['scan']['id'],
                    'occurrences': previous['occurrences'] if previous else 1, 'status': 'open'}
        for key, item in aggregated.items():
            p = self.root / 'triage' / (key + '.json')
            if p.exists():
                item['status'] = read_json(p)['history'][-1]['status']
        return list(aggregated.values())

    def triage(self, key, change):
        with file_lock(self.lock):
            if not any(f['id'] == key for f in self.findings()):
                raise KeyError(key)
            p = self.root / 'triage' / (key + '.json')
            data = read_json(p) if p.exists() else {'history': []}
            data['history'].append({**change.model_dump(), 'created_at': now()})
            atomic_json(p, data)
            return data
