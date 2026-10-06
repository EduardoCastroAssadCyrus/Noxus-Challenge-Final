import sys
from types import SimpleNamespace

import pytest

from noxus.agent import NoxusAgent
from noxus.scanner_help import installation_help, show_installation_help


def test_installed_tools_produce_no_installation_output(tmp_path):
    agent = SimpleNamespace(doctor=lambda: {'semgrep': True, 'gitleaks': True})
    assert installation_help(agent, tmp_path / 'config.json') == ''


@pytest.mark.parametrize('system', ['Windows', 'Linux'])
def test_guidance_is_read_only_and_uses_current_config(tmp_path, monkeypatch, system, capsys):
    monkeypatch.setattr('noxus.scanner_help.platform.system', lambda: system)
    config = tmp_path / "projeto d'Equipe" / 'config.json'
    agent = SimpleNamespace(doctor=lambda: {'semgrep': False, 'gitleaks': True})
    show_installation_help(agent, config)
    captured = capsys.readouterr()
    assert captured.out == ''
    assert str(config) in captured.err
    assert 'pip install' in captured.err
    assert 'winget install --exact --id Gitleaks.Gitleaks' not in captured.err
    assert not config.parent.exists()
    if system == 'Windows':
        assert "d''Equipe" in captured.err
        assert 'Scripts' in captured.err
    else:
        assert '--config' in captured.err and 'install-tools' in captured.err


def test_selected_scan_does_not_suggest_unrelated_tools(tmp_path, monkeypatch):
    monkeypatch.setattr('noxus.scanner_help.platform.system', lambda: 'Windows')
    agent = SimpleNamespace(doctor=lambda: {'semgrep': False, 'gitleaks': False})
    help_text = installation_help(agent, tmp_path / 'config.json', ['gitleaks'])
    assert 'winget install --exact --id Gitleaks.Gitleaks' in help_text
    assert 'semgrep' not in help_text


def test_doctor_does_not_mistake_perl_for_nikto(config, monkeypatch):
    config['commands']['nikto'] = ['perl', 'missing/nikto.pl']
    monkeypatch.setattr('noxus.agent.shutil.which', lambda _: sys.executable)
    assert NoxusAgent(config).doctor()['nikto'] is False


def test_windows_dependency_check_command(config, monkeypatch):
    monkeypatch.setattr('noxus.agent.platform.system', lambda: 'Windows')
    agent = NoxusAgent(config)
    assert agent.command_prefix('dependency-check') == ['dependency-check.bat']
    monkeypatch.setattr('noxus.agent.shutil.which', lambda name: None if name == 'java' else name)
    monkeypatch.setattr('noxus.agent.java_executable', lambda: None)
    assert agent.doctor()['dependency-check'] is False
