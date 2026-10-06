"""Executa o Agent irmão com o backend do dashboard como único receptor.

Este comando não inicia outra API, não importa demonstrações e não chama a IA.
Os scanners só são executados nos comandos scan/watch escolhidos pelo usuário.
"""

import argparse
import ipaddress
import json
import logging
import os
import runpy
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.agent_connection import ensure_ingestion_key  # noqa: E402
from app.core.config import get_settings  # noqa: E402


def main():
    parser = argparse.ArgumentParser(
        description="NoxusAgent conectado ao dashboard local"
    )
    parser.add_argument("action", choices=["init", "scan", "watch", "flush", "doctor"])
    parser.add_argument(
        "--config", type=Path, help="Configuração existente, sem sobrescrevê-la"
    )
    parser.add_argument(
        "--tools",
        nargs="+",
        choices=["semgrep", "gitleaks", "dependency-check", "nikto"],
    )
    args = parser.parse_args()
    if args.tools and args.action != "scan":
        parser.error("--tools só pode ser usado com scan.")
    settings = get_settings()
    project = settings.agent_project.resolve()
    if not (project / "noxus/agent.py").is_file():
        parser.error(
            "Agent não encontrado. Configure NOXUS_AGENT_PROJECT no backend/.env."
        )
    endpoint = urlsplit(settings.agent_api_url)
    try:
        local = (
            endpoint.hostname == "localhost"
            or ipaddress.ip_address(endpoint.hostname).is_loopback
        )
        _ = endpoint.port
    except (ValueError, TypeError):
        local = False
    if (
        not local
        or endpoint.scheme not in {"http", "https"}
        or endpoint.username
        or endpoint.password
        or endpoint.query
        or endpoint.fragment
        or endpoint.path not in {"", "/"}
    ):
        parser.error(
            "NOXUS_AGENT_API_URL deve ser uma origem HTTP(S) local, sem /api ou credenciais."
        )
    config_path = (
        args.config or settings.resolved_data_file.parent / "noxus-agent/config.json"
    ).resolve()
    sys.path.insert(0, str(project))
    try:
        import noxus.agent as agent_module
        from noxus.agent import NoxusAgent
        from noxus.scanner_help import show_installation_help
        from noxus.storage import atomic_json, read_json
    except ModuleNotFoundError as exc:
        raise RuntimeError("Instale as dependências com bun run setup:local.") from exc

    # Evita que a própria gravação de resultados/builds gere novas rodadas de monitoramento.
    agent_module.IGNORED.update(
        {
            ".data",
            ".venv-local",
            ".tmp",
            ".test-results",
            ".output",
            ".nitro",
            ".tanstack",
            ".ruff_cache",
        }
    )

    if args.action == "init":
        existing_registration = config_path.exists()
        if existing_registration:
            print("Cadastro existente encontrado; retomando a conexão com o backend.")
        else:
            # Reutiliza o cadastro interativo original: não inventamos desenvolvedor ou alvo.
            sys.argv = ["noxus", "--config", str(config_path), "init", "--no-install-help"]
            runpy.run_module("noxus.__main__", run_name="__main__")
        if not config_path.exists():
            raise RuntimeError("O cadastro do Agent não foi concluído.")
        config = read_json(config_path)
        config["api_url"] = settings.agent_api_url.rstrip("/")
        # Valida o cadastro salvo antes de sincronizar somente destino e chave.
        agent = NoxusAgent(config)
        try:
            config["api_key"] = ensure_ingestion_key(settings).get_secret_value()
            atomic_json(config_path, config)
        except OSError as exc:
            raise RuntimeError(
                "Cadastro preservado, mas não foi possível salvar a chave compartilhada."
            ) from exc
        print(f"Agent conectado ao receptor {config['api_url']}/api/findings.")
        print(f"Configuração: {config_path}")
        print("Mantenha bun run dev:api aberto. Não execute noxus serve neste fluxo.")
        show_installation_help(agent, config_path, compact=True)
        return

    if not config_path.is_file():
        parser.error(
            "Execute bun run agent:init primeiro, ou informe --config com seu arquivo existente."
        )
    config = read_json(config_path)
    # Sobreposição só em memória: permite usar um cadastro antigo sem modificar sua fila/configuração.
    config["api_url"] = settings.agent_api_url.rstrip("/")
    config["api_key"] = ensure_ingestion_key(settings).get_secret_value()
    os.environ["NOXUS_API_KEY"] = config["api_key"]
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    agent = NoxusAgent(config)
    if args.action in {"doctor", "scan", "watch"}:
        show_installation_help(agent, config_path, args.tools if args.action == "scan" else None)
    print(f"Receptor: {config['api_url']}/api/findings")
    if args.action == "doctor":
        print(json.dumps(agent.doctor(), ensure_ascii=False, indent=2))
    elif args.action == "flush":
        print(f"{agent.flush()} relatórios enviados.")
    elif args.action == "watch":
        agent.watch()
    elif args.action == "scan":
        results = agent.scan(args.tools)
        if any(result["scan"]["status"] != "completed" for result in results):
            return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nAgent encerrado. Relatórios pendentes permanecem na fila local.")
    except RuntimeError as exc:
        # Mensagens RuntimeError são nossas e não incluem material secreto.
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from None
    except (ValueError, TimeoutError, OSError, KeyError) as exc:
        # Exceções de bibliotecas podem conter chave ou evidências: mostrar apenas o tipo.
        print(
            f"Falha no Agent ({type(exc).__name__}). O cadastro e a fila foram preservados.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
