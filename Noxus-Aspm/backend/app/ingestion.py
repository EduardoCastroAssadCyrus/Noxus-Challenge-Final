"""Adapta um envelope validado ao dashboard sem inventar severidade ou autoria."""

import hashlib
import json
from datetime import datetime

from app.domain.models import Asset, Finding, FindingEvidence
from app.domain.scan_contract import ScanEnvelope


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def fingerprint(doc, finding):
    # Branch, ferramenta e produtor ficam separados; não correlacionamos scanners aqui.
    identity = [
        doc["asset"]["id"],
        doc["asset"]["repository_url"],
        doc["asset"]["branch"],
        doc["source"],
        doc["scan"]["tool"],
        finding["rule_id"],
        finding["location"],
        finding["dependency"],
    ]
    return "NX-" + digest(identity)


def normalize(envelope: ScanEnvelope, received_at: datetime):
    doc = envelope.model_dump(mode="json")
    items = {}
    for raw in doc["findings"]:
        identifier = fingerprint(doc, raw)
        if identifier in items:
            continue
        original = {key: value for key, value in doc.items() if key != "findings"}
        original["finding"] = raw
        items[identifier] = Finding(
            id=identifier,
            title=raw["title"],
            source=envelope.scan.category,
            producer=envelope.source,
            scan_id=str(envelope.scan.id),
            tool=envelope.scan.tool,
            asset_id=envelope.asset.id,
            asset_name=envelope.asset.name,
            technical_severity=raw["severity"],
            status="open",
            cve=", ".join(raw["cve"]) or None,
            file=raw["location"]["file"],
            line=raw["location"]["line"],
            priority_explanation="Prioridade operacional ainda não calculada.",
            detected_at=envelope.scan.finished_at,
            imported_at=received_at,
            correlated_count=1,
            correlation_status="matched",
            correlation_confidence=1,
            evidences=[
                FindingEvidence(
                    source=envelope.scan.category,
                    tool=envelope.scan.tool,
                    source_finding_id=raw["rule_id"],
                )
            ],
            description=raw["description"],
            remediation=raw["recommendation"] or "",
            original=original,
        )
    return list(items.values())


def imported_asset(envelope: ScanEnvelope, received_at: datetime):
    # O executor não é necessariamente dono do ativo ou autor da falha.
    # Contexto de negócio ausente fica não informado, para revisão manual.
    source = envelope.asset
    return Asset(
        id=source.id,
        name=source.name,
        application_name=source.name,
        type="application",
        identifier=source.id,
        repo=source.repository_url,
        environment="unknown",
        owner="Não informado",
        business_criticality=None,
        access="unknown",
        location={"hosting": "unknown", "provider": "Não informado", "region": "Não informada"},
        data_classification="unknown",
        contains_real_data=None,
        technologies=[],
        registration_source="integration",
        registry_status="pending_review",
        assessment_status="assessed" if envelope.scan.status != "failed" else "not_assessed",
        open_findings=0,
        last_seen_at=received_at,
        last_scan_at=envelope.scan.finished_at,
        scan_metadata=source.model_dump(mode="json"),
    )
