import os
from types import SimpleNamespace

from noxus.agent import NoxusAgent
from noxus import tool_paths


def test_local_scanners_without_path(config, monkeypatch):
    monkeypatch.setattr(tool_paths.platform, 'system', lambda: 'Windows')
    monkeypatch.setattr(tool_paths.shutil, 'which', lambda _: None)
    agent = NoxusAgent(config)
    root = agent.state.parent
    semgrep = root / 'scanners-venv/Scripts/semgrep.exe'
    dependency = root / 'tools/dependency-check/bin/dependency-check.bat'
    script = root / 'tools/nikto/program/nikto.pl'
    for path in (semgrep, dependency, script):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    monkeypatch.setattr(tool_paths, 'perl_executable', lambda: 'C:/Strawberry/perl/bin/perl.exe')
    assert agent.command_prefix('semgrep') == [str(semgrep.resolve())]
    assert agent.command_prefix('dependency-check') == [str(dependency.resolve())]
    assert agent.command_prefix('nikto') == ['C:/Strawberry/perl/bin/perl.exe', str(script.resolve())]
    assert config['commands'] == {}


def test_winget_gitleaks_outside_path(tmp_path, monkeypatch):
    monkeypatch.setattr(tool_paths.platform, 'system', lambda: 'Windows')
    monkeypatch.setattr(tool_paths.shutil, 'which', lambda _: None)
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path))
    executable = tmp_path / 'Microsoft/WinGet/Packages/Gitleaks.Gitleaks_test/gitleaks.exe'
    executable.parent.mkdir(parents=True)
    executable.touch()
    assert tool_paths.scanner_command('gitleaks', tmp_path / 'agent') == [str(executable.resolve())]


def test_java_uses_supported_version_and_only_changes_child_environment(tmp_path, monkeypatch):
    monkeypatch.setattr(tool_paths.platform, 'system', lambda: 'Windows')
    old = tmp_path / 'old/bin/java.exe'
    new = tmp_path / 'programs/Eclipse Adoptium/jdk-21/bin/java.exe'
    for path in (old, new):
        path.parent.mkdir(parents=True)
        path.touch()
    monkeypatch.setenv('JAVA_HOME', str(old.parent.parent))
    monkeypatch.setenv('ProgramFiles', str(tmp_path / 'programs'))
    monkeypatch.setattr(tool_paths.shutil, 'which', lambda _: str(old))
    monkeypatch.setattr(tool_paths.subprocess, 'run', lambda args, **kwargs: SimpleNamespace(
        returncode=0, stdout='', stderr='java version "1.8.0"' if args[0] == str(old) else 'openjdk version "21.0.1"'
    ))
    previous_home = os.environ['JAVA_HOME']
    environment = tool_paths.java_environment()
    assert environment['JAVACMD'] == str(new.resolve())
    assert environment['JAVA_HOME'] == str(new.parent.parent)
    assert os.environ['JAVA_HOME'] == previous_home
