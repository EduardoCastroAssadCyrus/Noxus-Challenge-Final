"""Instruções de instalação: apenas texto, sem downloads ou execução automática."""

import json
import platform
import shlex
import sys
from pathlib import Path


def ps_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def installation_help(agent, config_path, tools=None, compact=False):
    status = agent.doctor()
    missing = [tool for tool in (tools or status) if not status[tool]]
    if not missing:
        return ""
    config_path = Path(config_path).resolve()
    state = config_path.parent
    venv = state / "scanners-venv"
    root = state / "tools"
    lines = [
        "\nScanners ausentes ou com comando inválido: " + ", ".join(missing),
        "Execute os comandos abaixo para instalar. Nada é instalado automaticamente.",
        "Se já instalou, confira PATH e commands no cadastro: " + str(config_path),
    ]
    system = platform.system()
    if compact:
        lines = ["\nInstalação dos scanners ausentes:"]
    if system == "Windows":
        if not compact:
            lines += [
                "\nPowerShell (winget precisa estar disponível):",
                "Após instalar Java/Perl/Git/Gitleaks, reabra o terminal para atualizar o PATH.",
            ]
        commands = {}
        if "semgrep" in missing:
            python = venv / "Scripts/python.exe"
            lines += [
                "\n# SAST — Semgrep",
                f"& {ps_quote(sys.executable)} -m venv {ps_quote(venv)}",
                f"& {ps_quote(python)} -m pip install semgrep",
            ]
            commands["semgrep"] = [str(venv / "Scripts/semgrep.exe")]
        if "gitleaks" in missing:
            lines += ["\n# Segredos — Gitleaks", "winget install --exact --id Gitleaks.Gitleaks"]
            commands["gitleaks"] = ["gitleaks"]
        if "dependency-check" in missing or "nikto" in missing:
            lines += [f"New-Item -ItemType Directory -Force -Path {ps_quote(root)} | Out-Null"]
        if "dependency-check" in missing:
            archive = root / "dependency-check.zip"
            lines += [
                "\n# SCA — Dependency-Check",
                "winget install --exact --id EclipseAdoptium.Temurin.21.JDK",
                "$noxusRelease = Invoke-RestMethod 'https://api.github.com/repos/dependency-check/DependencyCheck/releases/latest'",
                "$noxusZip = $noxusRelease.assets | Where-Object { $_.name -like '*-release.zip' } | Select-Object -First 1",
                "if (-not $noxusZip) { throw 'ZIP do Dependency-Check não encontrado.' }",
                f"Invoke-WebRequest -Uri $noxusZip.browser_download_url -OutFile {ps_quote(archive)}",
                f"Expand-Archive -LiteralPath {ps_quote(archive)} -DestinationPath {ps_quote(root)} -Force",
            ]
            commands["dependency-check"] = [str(root / "dependency-check/bin/dependency-check.bat")]
        if "nikto" in missing:
            destination = ps_quote(root / "nikto")
            lines += [
                "\n# DAST — Nikto",
                "winget install --exact --id Git.Git",
                "winget install --exact --id StrawberryPerl.StrawberryPerl",
                "# Reabra o terminal após instalar Git e Perl, antes do comando seguinte.",
                f"if (-not (Test-Path -LiteralPath {destination})) {{ git clone --depth 1 https://github.com/sullo/nikto.git {destination} }}",
                "# Se a pasta já existe, confira se program/nikto.pl está presente.",
            ]
            commands["nikto"] = ["perl", str(root / "nikto/program/nikto.pl")]
        if not compact:
            lines += [
                "\nNo config.json, mescle estas entradas em commands, preservando as demais:",
                json.dumps({"commands": commands}, ensure_ascii=False, indent=2),
                "Confira novamente com doctor. A presença do executável não garante que o scan concluirá.",
            ]
    elif system == "Linux":
        python = shlex.quote(str(venv / "bin/python"))
        package = shlex.quote(str(Path(__file__).resolve().parents[1]))
        lines += [
            "\n# SAST: Semgrep | DAST: Nikto | SCA: Dependency-Check | Segredos: Gitleaks",
            "sudo apt update",
            "sudo apt install -y python3-venv git openjdk-21-jre-headless perl libnet-ssleay-perl libio-socket-ssl-perl libwww-perl",
            "# Instala os scanners em um ambiente separado e atualiza este mesmo cadastro:",
            f"{shlex.quote(sys.executable)} -m venv {shlex.quote(str(venv))}",
            f"{python} -m pip install -e {package}",
            f"{python} -m noxus --config {shlex.quote(str(config_path))} install-tools",
            "Se commands contém um caminho antigo, corrija-o ou remova só a entrada inválida antes de instalar.",
            "Execute doctor novamente após a instalação.",
        ]
    else:
        lines += [
            "O instalador automático atende Linux/WSL. Consulte a instalação oficial:",
            "https://semgrep.dev/products/community-edition",
            "https://github.com/gitleaks/gitleaks",
            "https://dependency-check.github.io/DependencyCheck/dependency-check-cli/",
            "https://github.com/sullo/nikto",
        ]
    if compact:
        lines += ["\nApós instalar, execute doctor para conferir os caminhos e configurar commands."]
    return "\n".join(lines)


def show_installation_help(agent, config_path, tools=None, compact=False):
    text = installation_help(agent, config_path, tools, compact=compact)
    if text:
        # Mantém stdout do doctor como JSON para quem usa o comando em scripts.
        print(text, file=sys.stdout if compact else sys.stderr)
