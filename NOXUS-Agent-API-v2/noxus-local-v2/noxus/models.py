"""Contrato compartilhado pela API, NoxusAgent e futura extensão Noxus."""
from datetime import datetime
from typing import Literal, Annotated
from urllib.parse import urlsplit
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

# EXTENSÃO NOXUS: fork futuro do SonarQube for IDE. Não é o Agent Python.
NOXUS_VSCODE_EXTENSION_SOURCE = 'noxus-vscode-extension'
NOXUS_AGENT_SOURCE = 'noxus-agent'
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1024)]
Category = Literal['SAST', 'DAST', 'SCA', 'SECRET', 'EXTENSION']
Status = Literal['open', 'in_progress', 'resolved', 'false_positive', 'accepted_risk']
TOOL_CATEGORIES = {'semgrep': 'SAST', 'gitleaks': 'SECRET', 'dependency-check': 'SCA', 'nikto': 'DAST', 'sonar': 'SAST', 'dependency-reputation': 'SCA', 'extension-reputation': 'EXTENSION'}

def safe_url(value):
    if value is None:
        return value
    p = urlsplit(value)
    if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password or p.query or p.fragment:
        raise ValueError('URL HTTP(S) sem credenciais, query ou fragmento é obrigatória.')
    _ = p.port
    return value

class Model(BaseModel):
    model_config = ConfigDict(extra='forbid', validate_default=True)

class Developer(Model):
    name: Text
    role: Text | None = None
    team: Text | None = None

class ConsumedAPI(Model):
    name: Text
    base_url: Text
    source: Literal['manual', 'detected'] = 'manual'
    _url = field_validator('base_url')(safe_url)

class Asset(Model):
    id: Text
    name: Text
    type: Text = 'web-api'
    repository_url: Text | None = None
    branch: Text = 'main'
    commit: Annotated[str, StringConstraints(pattern=r'^[0-9a-fA-F]{7,64}$')] | None = None
    local_ip: Text | None = None
    application_url: Text | None = None
    consumed_apis: list[ConsumedAPI] = Field(default_factory=list, max_length=100)
    _urls = field_validator('repository_url', 'application_url')(safe_url)

class Scan(Model):
    id: UUID
    tool: Literal['semgrep', 'gitleaks', 'dependency-check', 'nikto', 'sonar', 'dependency-reputation', 'extension-reputation']
    tool_version: Text | None = None
    category: Category
    started_at: datetime
    finished_at: datetime
    status: Literal['completed', 'partial', 'failed']
    trigger: Literal['manual', 'startup', 'file-change', 'dependency-change', 'commit', 'app-online', 'scheduled', 'ide-save', 'ide-change', 'extension-change'] = 'manual'
    error: Annotated[str, StringConstraints(max_length=2000)] | None = None

    @model_validator(mode='after')
    def check(self):
        if any(d.tzinfo is None or d.utcoffset() is None for d in (self.started_at, self.finished_at)):
            raise ValueError('Datas precisam incluir fuso horário.')
        if self.finished_at < self.started_at:
            raise ValueError('Término anterior ao início.')
        if TOOL_CATEGORIES[self.tool] != self.category:
            raise ValueError('Categoria incompatível com ferramenta.')
        if self.status == 'failed' and not self.error:
            raise ValueError('Varredura com falha exige error.')
        return self

class Location(Model):
    file: Text | None = None
    line: int | None = Field(None, ge=1, strict=True)
    column: int | None = Field(None, ge=1, strict=True)
    url: Text | None = None
    _url = field_validator('url')(safe_url)

class Dependency(Model):
    name: Text
    version: Text | None = None
    ecosystem: Text | None = None

class Finding(Model):
    title: Text
    description: str = Field('', max_length=8000)
    rule_id: Text
    severity: Literal['critical', 'high', 'medium', 'low', 'info'] | None = None
    cwe: list[Annotated[str, StringConstraints(pattern=r'^CWE-\d+$')]] = Field(default_factory=list, max_length=100)
    cve: list[Annotated[str, StringConstraints(pattern=r'^CVE-\d{4}-\d{4,}$')]] = Field(default_factory=list, max_length=100)
    location: Location
    dependency: Dependency | None = None
    recommendation: str | None = Field(None, max_length=8000)
    @model_validator(mode='after')
    def check(self):
        if not (self.location.file or self.location.url or self.dependency):
            raise ValueError('Informe arquivo, URL ou dependência/extensão.')
        if (self.location.line or self.location.column) and not self.location.file:
            raise ValueError('Linha/coluna exige arquivo.')
        return self

class ScanEnvelope(Model):
    schema_version: Literal['1.0'] = '1.0'
    source: Literal['noxus-agent', 'noxus-vscode-extension']
    developer: Developer
    asset: Asset
    scan: Scan
    findings: list[Finding] = Field(max_length=20000)
    @model_validator(mode='after')
    def check(self):
        agent_tools = {'semgrep', 'gitleaks', 'dependency-check', 'nikto'}
        if self.source == NOXUS_AGENT_SOURCE and self.scan.tool not in agent_tools:
            raise ValueError('Ferramenta não pertence ao NoxusAgent.')
        # EXTENSÃO NOXUS: Sonar, dependências, extensões e secret scanning futuro.
        if self.source == NOXUS_VSCODE_EXTENSION_SOURCE and self.scan.tool not in {'sonar', 'dependency-reputation', 'extension-reputation', 'gitleaks'}:
            raise ValueError('Ferramenta não suportada pela integração da extensão Noxus.')
        if self.scan.status == 'failed' and self.findings:
            raise ValueError('Falha total não aceita findings; use partial.')
        if self.scan.category == 'SECRET':
            for f in self.findings:
                f.title = 'Possível credencial exposta'
                f.description = 'Evidência sensível omitida; investigue localmente.'
                f.recommendation = 'Confirme e rotacione a credencial exposta.'
        return self

class Triage(Model):
    status: Status
    actor: Text
    reason: Annotated[str, StringConstraints(min_length=3, max_length=2000)]
