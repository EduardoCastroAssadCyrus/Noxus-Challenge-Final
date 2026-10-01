"""Chave local compartilhada entre o Agent e o receptor, nunca enviada ao frontend."""

import json
import os
import secrets

from pydantic import SecretStr

from app.core.local_lock import local_store_lock


def connection_file(settings):
    return settings.resolved_data_file.parent / "agent-connection.json"


def read_ingestion_key(settings):
    # Uma chave explícita no backend/.env tem prioridade sobre a chave local gerada.
    if settings.ingestion_api_key:
        return settings.ingestion_api_key
    path = connection_file(settings)
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))["api_key"]
        if not isinstance(value, str) or not value:
            raise ValueError
    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError("Configuração local do Agent inválida; restaure seu backup.") from exc
    return SecretStr(value)


def ensure_ingestion_key(settings):
    path = connection_file(settings)
    with local_store_lock(path):
        current = read_ingestion_key(settings)
        if current:
            return current
        value = secrets.token_urlsafe(32)
        temporary = path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump({"api_key": value}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
        return SecretStr(value)
