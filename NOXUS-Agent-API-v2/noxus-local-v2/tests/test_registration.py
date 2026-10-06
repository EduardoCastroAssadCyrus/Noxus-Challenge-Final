import json
import sys

import pytest

from noxus.__main__ import main
from noxus.agent import NoxusAgent, local_repository_path


@pytest.mark.parametrize('quote', ['', chr(34), chr(39)])
def test_init_accepts_local_folder_without_remote(tmp_path, monkeypatch, quote):
    repo = tmp_path / 'Projeto com espaços'
    repo.mkdir()
    config_path = tmp_path / 'config.json'
    answers = iter([f'{quote}{repo}{quote}', 'Dev', '', '', '', '', ''])
    monkeypatch.setattr('builtins.input', lambda _: next(answers))
    monkeypatch.setattr(sys, 'argv', ['noxus', '--config', str(config_path), 'init'])
    main()
    config = json.loads(config_path.read_text(encoding='utf-8'))
    assert config['repository_path'] == str(repo.resolve())
    assert config['asset']['repository_url'] is None
    # Configurações editadas à mão também aceitam as aspas externas.
    config['repository_path'] = f'{quote}{repo}{quote}'
    assert NoxusAgent(config).repo == repo.resolve()


def test_local_folder_must_exist(tmp_path):
    with pytest.raises(ValueError, match='não existe'):
        local_repository_path(tmp_path / 'inexistente')


@pytest.mark.parametrize('omit', [True, False])
def test_agent_api_accepts_missing_remote(client, payload, headers, omit):
    if omit:
        payload['asset'].pop('repository_url')
    else:
        payload['asset']['repository_url'] = None
    response = client.post('/api/findings', json=payload, headers=headers)
    assert response.status_code in (200, 201), response.text
