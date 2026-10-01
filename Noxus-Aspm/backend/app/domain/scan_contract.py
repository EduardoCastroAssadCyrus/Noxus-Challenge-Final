"""Contrato NOXUS v2 (schema 1.0), compartilhado com Agent e extensão.

source identifica o produtor; scan.category identifica o tipo da análise.
Relatórios brutos e campos extras não pertencem a este contrato.
"""

from datetime import datetime
from typing import Annotated, Literal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1024)]
Category = Literal["SAST", "DAST", "SCA", "SECRET", "EXTENSION"]
TOOL_CATEGORIES = {
    "semgrep": "SAST",
    "gitleaks": "SECRET",
    "dependency-check": "SCA",
    "nikto": "DAST",
    "sonar": "SAST",
    "dependency-reputation": "SCA",
    "extension-reputation": "EXTENSION",
}


def safe_url(value):
    if value is None:
        return value
    parsed = urlsplit(value)
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("URL HTTP(S) sem credenciais, query ou fragmento é obrigatória.")
    _ = parsed.port
    return value


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_default=True)


class Developer(ContractModel):
    name: Text
    role: Text | None = None
    team: Text | None = None


class ConsumedAPI(ContractModel):
    name: Text
    base_url: Text
    source: Literal["manual", "detected"] = "manual"
    _url = field_validator("base_url")(safe_url)


class ScanAsset(ContractModel):
    id: Text
    name: Text
    type: Text = "web-api"
    repository_url: Text
    branch: Text = "main"
    commit: Annotated[str, StringConstraints(pattern=r"^[0-9a-fA-F]{7,64}$")] | None = None
    local_ip: Text | None = None
    application_url: Text | None = None
    consumed_apis: list[ConsumedAPI] = Field(default_factory=list, max_length=100)
    _urls = field_validator("repository_url", "application_url")(safe_url)


class Scan(ContractModel):
    id: UUID
    tool: Literal[
        "semgrep",
        "gitleaks",
        "dependency-check",
        "nikto",
        "sonar",
        "dependency-reputation",
        "extension-reputation",
    ]
    tool_version: Text | None = None
    category: Category
    started_at: datetime
    finished_at: datetime
    status: Literal["completed", "partial", "failed"]
    trigger: Literal[
        "manual",
        "startup",
        "file-change",
        "dependency-change",
        "commit",
        "app-online",
        "scheduled",
        "ide-save",
        "ide-change",
        "extension-change",
    ] = "manual"
    error: Annotated[str, StringConstraints(max_length=2000)] | None = None

    @model_validator(mode="after")
    def check(self):
        if any(
            d.tzinfo is None or d.utcoffset() is None for d in (self.started_at, self.finished_at)
        ):
            raise ValueError("Datas precisam incluir fuso horário.")
        if self.finished_at < self.started_at:
            raise ValueError("Término anterior ao início.")
        if TOOL_CATEGORIES[self.tool] != self.category:
            raise ValueError("Categoria incompatível com ferramenta.")
        if self.status == "failed" and not (self.error and self.error.strip()):
            raise ValueError("Varredura com falha exige error.")
        return self


class Location(ContractModel):
    file: Text | None = None
    line: int | None = Field(None, ge=1, strict=True)
    column: int | None = Field(None, ge=1, strict=True)
    url: Text | None = None
    _url = field_validator("url")(safe_url)


class Dependency(ContractModel):
    name: Text
    version: Text | None = None
    ecosystem: Text | None = None


class ScanFinding(ContractModel):
    title: Text
    description: str = Field("", max_length=8000)
    rule_id: Text
    severity: Literal["critical", "high", "medium", "low", "info"] | None = None
    cwe: list[Annotated[str, StringConstraints(pattern=r"^CWE-\d+$")]] = Field(
        default_factory=list, max_length=100
    )
    cve: list[Annotated[str, StringConstraints(pattern=r"^CVE-\d{4}-\d{4,}$")]] = Field(
        default_factory=list, max_length=100
    )
    location: Location
    dependency: Dependency | None = None
    recommendation: str | None = Field(None, max_length=8000)

    @model_validator(mode="after")
    def check(self):
        if not (self.location.file or self.location.url or self.dependency):
            raise ValueError("Informe arquivo, URL ou dependência/extensão.")
        if (self.location.line or self.location.column) and not self.location.file:
            raise ValueError("Linha/coluna exige arquivo.")
        return self


class ScanEnvelope(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    source: Literal["noxus-agent", "noxus-vscode-extension"]
    developer: Developer
    asset: ScanAsset
    scan: Scan
    findings: list[ScanFinding] = Field(max_length=20000)

    @model_validator(mode="after")
    def check(self):
        allowed = (
            {"semgrep", "gitleaks", "dependency-check", "nikto"}
            if self.source == "noxus-agent"
            else {"sonar", "dependency-reputation", "extension-reputation", "gitleaks"}
        )
        if self.scan.tool not in allowed:
            raise ValueError("Ferramenta incompatível com o produtor informado em source.")
        if self.scan.status == "failed" and self.findings:
            raise ValueError("Falha total não aceita findings; use partial.")
        # Sanitizar antes de persistir ou enviar à IA; não guardar os textos livres de SECRET.
        if self.scan.category == "SECRET":
            for finding in self.findings:
                finding.title = "Possível credencial exposta"
                finding.description = "Evidência sensível omitida; investigue localmente."
                finding.recommendation = "Confirme e rotacione a credencial exposta."
        return self
