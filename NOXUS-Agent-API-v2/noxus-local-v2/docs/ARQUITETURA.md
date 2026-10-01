# Arquitetura para revisão

`noxus/models.py`: contrato Pydantic compartilhado. Constants `NOXUS_AGENT_SOURCE` e **`NOXUS_VSCODE_EXTENSION_SOURCE`** são distintas. Campos extras são rejeitados. Datas exigem timezone. Categorias são validadas contra a ferramenta.

`noxus/agent.py`: subprocessos sem shell, tempo máximo, relatórios temporários, normalização, fila e monitoramento. `run_scan` grava resultado antes de qualquer tentativa HTTP. `flush` apaga a fila só após confirmação do ID. Relatórios brutos vivem em diretório temporário e são removidos normalmente ao sair; encerramento abrupto do processo pode deixar temporários no SO.

`noxus/parsers.py`: adaptadores allowlist de Semgrep, Gitleaks, Dependency-Check e Nikto. Severidade ausente fica null. CVE/CWE só vêm dos relatórios. Nenhuma IA faz inferência nesta camada.

`noxus/api.py`: app factory; valida o mesmo contrato para Agent e extensão. A rota explicitamente nomeada da EXTENSÃO NOXUS verifica source. A chave autentica o cliente local; `source`, `actor` e nome do desenvolvedor são declarados pelo cliente, não constituem identidade corporativa verificada.

`noxus/storage.py`: armazenamento JSON isolado. Arquivos de scan são imutáveis; triagem tem histórico independente. Consultas calculam agregados. Locks protegem escrita concorrente e substituição atômica evita leitura parcial. Use filesystem local, não compartilhamento de rede.

`noxus/installer.py`: Linux/WSL, instalação explícita por fontes oficiais. Downloads/release latest não estão fixados; registro de instalação auxilia revisão. Checksum Gitleaks e digest de release quando disponível; HTTPS não é garantia absoluta de integridade da cadeia de suprimentos.

`noxus/__main__.py`: CLI, configuração, API, demonstração e monitor em segundo plano.

A API recebe apenas relatórios normalizados. A normalização migrou do servidor v1 para os clientes nesta v2, conforme a decisão mais recente do projeto. A extensão futura também normaliza localmente.

## Limites deliberados do protótipo

Sem multi-tenant, serviço de boot, fila distribuída, correlação entre scanners, captura de diagnostics da extensão, descoberta completa de APIs, importador v1 ou integração CrewAI. Deduplicação determinística preserva diferença de ferramenta e origem. Não resolve achados automaticamente por ausência em scans.

Eventos Git são detectados por polling de HEAD, após commit. Não existe garantia pré-commit/bloqueio. Scans de código leem working tree. O commit registrado é contexto, não um snapshot imutável dos arquivos analisados.
