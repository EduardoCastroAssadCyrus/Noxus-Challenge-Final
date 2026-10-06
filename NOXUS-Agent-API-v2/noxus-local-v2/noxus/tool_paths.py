"""Localiza ferramentas instaladas sem alterar o PATH global ou o cadastro."""

import os
import platform
import re
import shutil
import subprocess
from pathlib import Path


def executable(path):
    return str(path.resolve()) if path.is_file() else None


def perl_executable():
    found = shutil.which('perl')
    if found:
        return found
    if platform.system() == 'Windows':
        return executable(Path(os.environ.get('SystemDrive', 'C:') + '/Strawberry/perl/bin/perl.exe'))
    return None


def scanner_command(tool, state):
    windows = platform.system() == 'Windows'
    root = state.parent
    suffix = '.exe' if windows else ''
    bin_dir = 'Scripts' if windows else 'bin'
    if tool == 'semgrep':
        found = executable(root / 'scanners-venv' / bin_dir / ('semgrep' + suffix))
        if found:
            return [found]
    if tool == 'gitleaks':
        found = executable(root / 'tools' / ('gitleaks' + suffix))
        if not found and windows and os.environ.get('LOCALAPPDATA'):
            winget = Path(os.environ['LOCALAPPDATA']) / 'Microsoft/WinGet'
            found = executable(winget / 'Links/gitleaks.exe')
            if not found:
                for path in sorted((winget / 'Packages').glob('Gitleaks.Gitleaks_*/gitleaks.exe')):
                    found = executable(path)
                    if found:
                        break
        if found:
            return [found]
    if tool == 'nikto':
        script = root / 'tools/nikto/program/nikto.pl'
        perl = perl_executable()
        if script.is_file() and perl:
            return [perl, str(script.resolve())]
    name = 'dependency-check.bat' if windows else 'dependency-check.sh'
    if tool == 'dependency-check':
        found = executable(root / 'tools/dependency-check/bin' / name)
        if found:
            return [found]
    name = name if tool == 'dependency-check' else tool
    return [shutil.which(name) or name]


def java_executable():
    candidates = []
    if os.environ.get('JAVA_HOME'):
        candidates.append(Path(os.environ['JAVA_HOME']) / 'bin' / ('java.exe' if os.name == 'nt' else 'java'))
    if platform.system() == 'Windows':
        program_files = Path(os.environ.get('ProgramFiles', 'C:/Program Files'))
        candidates.extend(sorted((program_files / 'Eclipse Adoptium').glob('jdk-*/bin/java.exe'), reverse=True))
    found = shutil.which('java')
    if found:
        candidates.append(Path(found))
    for candidate in dict.fromkeys(candidates):
        if not candidate.is_file():
            continue
        try:
            result = subprocess.run([str(candidate), '-version'], capture_output=True, text=True, timeout=5)
            match = re.search(r'version\s+"(\d+)(?:\.(\d+))?', result.stderr + result.stdout)
            if match:
                major = int(match[2]) if match[1] == '1' and match[2] else int(match[1])
                if result.returncode == 0 and major >= 17:
                    return str(candidate.resolve())
        except (OSError, subprocess.TimeoutExpired):
            continue
    return None


def java_environment():
    java = java_executable()
    if not java:
        raise ValueError('Java 17 ou superior não encontrado. Execute doctor.')
    environment = os.environ.copy()
    environment['JAVA_HOME'] = str(Path(java).parent.parent)
    environment['JAVACMD'] = java
    environment['PATH'] = str(Path(java).parent) + os.pathsep + environment.get('PATH', '')
    return environment
