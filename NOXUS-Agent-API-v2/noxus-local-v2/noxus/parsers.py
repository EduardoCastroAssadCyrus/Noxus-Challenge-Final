"""Normalização LOCAL: copia somente campos permitidos, nunca o relatório bruto."""
import re
from urllib.parse import urljoin, urlsplit, urlunsplit
from noxus.models import Finding


def clean_url(value):
    p = urlsplit(value)
    host = p.hostname or ''
    if ':' in host:
        host = '[' + host + ']'
    if p.port:
        host += ':' + str(p.port)
    return urlunsplit((p.scheme, host, p.path, '', ''))

def severity(value):
    value = str(value or '').lower()
    return {'error': 'high', 'warning': 'medium', 'informational': 'info', 'moderate': 'medium'}.get(value, value if value in {'critical','high','medium','low','info'} else None)

def cwes(value):
    return sorted(set(re.findall(r'CWE-\d+', str(value))))

def normalize(tool, raw, target=None):
    findings = []
    partial = False
    if tool == 'semgrep':
        partial = bool(raw.get('errors'))
        for r in raw['results']:
            x = r.get('extra', {})
            findings.append(dict(title=r['check_id'], rule_id=r['check_id'], description=x.get('message',''),
                severity=severity(x.get('severity')), cwe=cwes(x.get('metadata',{}).get('cwe',[])),
                location={'file': r['path'], 'line': r['start']['line'], 'column': r['start'].get('col')}))
    elif tool == 'gitleaks':
        if not isinstance(raw, list):
            raise ValueError('Gitleaks deve retornar lista.')
        for r in raw:
            # Não copiar Secret, Match, Email, Author ou conteúdo de código.
            findings.append(dict(title='Possível credencial exposta', rule_id=r['RuleID'],
                description='Evidência sensível omitida; investigue localmente.', severity='high',
                location={'file':r['File'], 'line':r.get('StartLine')}))
    elif tool == 'dependency-check':
        partial = bool(raw.get('scanInfo', {}).get('analysisExceptions'))
        for dep in raw['dependencies']:
            for v in dep.get('vulnerabilities', []):
                name = v['name']
                findings.append(dict(title=name, rule_id=name, description=v.get('description',''),
                    severity=severity(v.get('severity')), cwe=cwes(v.get('cwes',[])),
                    cve=[name] if re.fullmatch(r'CVE-\d{4}-\d{4,}',name) else [],
                    location={'file':dep.get('filePath',dep.get('fileName'))},
                    dependency={'name':dep['fileName'], 'version':dep.get('version')}))
    elif tool == 'nikto':
        hosts = raw if isinstance(raw, list) else [raw]
        for host in hosts:
            for r in host['vulnerabilities']:
                rule = str(r['id'])
                uri = r.get('url') or r.get('uri')
                if not uri:
                    raise ValueError('Nikto sem URL.')
                findings.append(dict(title='Nikto '+rule, rule_id=rule, description=r.get('msg',r.get('message','')),
                    severity=severity(r.get('severity')), location={'url':clean_url(urljoin(target or '',uri))}))
    else:
        raise ValueError('Scanner desconhecido.')
    return [Finding.model_validate(f) for f in findings], partial
