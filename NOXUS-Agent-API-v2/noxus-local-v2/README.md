# NOXUS Local v2 — NoxusAgent + API JSON

Tudo roda na mesma máquina. O Agent executa scanners, normaliza relatórios e envia à API local. A API salva JSONs e oferece consultas e triagem. Não exige PostgreSQL, SQLite, Docker ou um servidor de banco. O Dependency-Check mantém seu próprio cache/base interna de CVEs; isso é independente do armazenamento Noxus.

## Comece aqui — Windows, sem scanners, para testar a API

### Ajuda para instalar scanners

`init`, `doctor`, `scan` e `watch` mostram instruções quando um scanner não é encontrado. No fluxo integrado, use `bun run agent:doctor` na raiz `Noxus-Aspm`.

No Windows, a ajuda imprime comandos PowerShell para Semgrep (pip em ambiente separado), Gitleaks (winget), Dependency-Check (Java e ZIP oficial) e Nikto (Git e Perl). Também mostra as entradas de `commands` a mesclar no seu `config.json`. Após instalar, reabra o terminal e execute `doctor` novamente. No Linux/WSL, mostra os comandos para o instalador existente. Nada é instalado automaticamente. A detecção verifica executáveis e pré-requisitos básicos; não executa os scanners.

Referências: [Semgrep](https://semgrep.dev/products/community-edition), [Gitleaks no winget](https://github.com/microsoft/winget-pkgs/tree/master/manifests/g/Gitleaks/Gitleaks), [Dependency-Check CLI](https://dependency-check.github.io/DependencyCheck/dependency-check-cli/), [Nikto](https://github.com/sullo/nikto).

### Iniciar a API independente

Requer Python 3.11 ou superior. Extraia o ZIP e abra a pasta `noxus-local-v2` no terminal do VS Code.

```powershell
cd "C:\Users\jacki\Documents\Faculdade e tals\Challenge\Noxus-Aspm"
bun run agent:init
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m noxus init
.\.venv\Scripts\python.exe -m noxus serve
```

O `init` pergunta: pasta **local** do projeto (com ou sem aspas; não clona o repositório), nome, cargo, equipe, URL HTTPS opcional do repositório, nome do ativo e URL da aplicação. Pressione Enter na URL do repositório para analisar somente a pasta local, sem GitHub. Deixe a aplicação vazia se ainda não houver. A API usa porta 8000; o aplicativo analisado pelo Nikto deve usar outra porta, por exemplo 8080.

Em outro terminal, na mesma pasta:

```powershell
.\.venv\Scripts\python.exe -m noxus demo
```

Abra http://127.0.0.1:8000/docs. Esse comando envia uma vulnerabilidade **fictícia**, identificada como demonstração; não executa scanners. Para consultas protegidas, preencha o parâmetro `x-api-key` com `api_key` do arquivo `.noxus/config.json`.

Os resultados estão em `.noxus/dados/scans/`. Não há banco a instalar. A configuração contém uma chave local gerada aleatoriamente; mantenha `.noxus/` fora do Git. A variável `NOXUS_API_KEY`, quando definida, substitui a chave no arquivo tanto no Agent quanto no comando `serve`.

## Quatro scanners — Linux/WSL recomendado para este MVP

Para o conjunto completo, use Ubuntu no WSL e execute **API e Agent dentro do mesmo WSL**. Isso evita divergências de localhost, PATH e arquivos entre Windows e Linux. O funcionamento nativo dos quatro scanners no Windows não foi validado. API/contrato são Python multiplataforma, com testes executados em Linux.

No Ubuntu/WSL, instale os pré-requisitos:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git perl openjdk-17-jre-headless
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m noxus init
.venv/bin/python -m noxus install-tools
.venv/bin/python -m noxus doctor
```

O instalador verifica ferramentas disponíveis e baixa as ausentes de fontes oficiais: PyPI (Semgrep), GitHub Gitleaks (com checksum), GitHub Nikto e releases Dependency-Check. Downloads exigem internet. Registra versões/commit quando disponíveis em `.noxus/tools/installed.json`. As releases são resolvidas no momento da instalação; essa instalação online não foi executada no ambiente de entrega. `doctor` verifica a disponibilidade dos comandos; não substitui uma varredura real.

Dependendo da versão do Dependency-Check e dos analisadores ativados, podem ser necessários pré-requisitos adicionais. A primeira atualização de CVEs pode ser demorada; consultas NVD sem chave podem sofrer limitação. Não é necessário configurar banco Noxus. Consulte a documentação oficial da ferramenta caso o scan falhe.

Em dois terminais:

```bash
# Terminal 1
.venv/bin/python -m noxus serve
```

```bash
# Terminal 2: varredura única
.venv/bin/python -m noxus scan
# Ou apenas ferramentas selecionadas
.venv/bin/python -m noxus scan --tools semgrep gitleaks
# Monitoramento contínuo; Ctrl+C encerra
.venv/bin/python -m noxus watch
```

Para segundo plano: `.venv/bin/python -m noxus start`. O comando informa o PID e grava `.noxus/agent/agent.log`; encerre esse processo pelo gerenciador de processos ou `kill PID` no Linux. `start` não configura serviço de inicialização do sistema. Existe lock para impedir dois monitores/varreduras simultâneos com a mesma configuração. Se outro já estiver ativo, o novo processo registrará o erro no log.

## O que o Agent faz

- Configuração inicial persistente: desenvolvedor, equipe, cargo, projeto e alvo.
- Verificação e instalação explícita das ferramentas ausentes com `install-tools`.
- Semgrep: SAST; Gitleaks: segredos no diretório atual (não no histórico Git inteiro); Dependency-Check: dependências; Nikto: aplicação HTTP local.
- Normalização no PC local para o contrato de `docs/scan-envelope.schema.json`.
- Remoção de `Secret`, `Match`, snippets, autor e e-mail dos relatórios Gitleaks; redaction também solicitado na execução do scanner.
- Um JSON por ferramenta/execução. Falha total = `failed`, lista vazia e mensagem de erro; erros internos reconhecidos no relatório = `partial`.
- Fila persistente e reenvio automático enquanto `watch` está ativo. Para envio manual: `python -m noxus flush`.
- Monitoramento por polling de arquivos, manifests e HEAD Git, com debounce de 3 segundos. Não modifica hooks e não bloqueia commits.
- Nikto quando a porta configurada passa de offline para online; não roda repetidamente enquanto permanecer online. A detecção observa TCP, não garante que a aplicação esteja pronta. Reinicializações mais rápidas que o intervalo podem passar despercebidas.
- SCA periódico a cada 24h durante o monitoramento, além da inicialização e alteração de dependências.

Scanners rodam sequencialmente. Durante um scan longo, eventos não são observados imediatamente; o próximo ciclo verifica o estado final dos arquivos. Um scan pode refletir arquivos alterados durante a execução. Não é análise instantânea por tecla, que pertence à futura extensão.

## JSON e configuração

`examples/agent-semgrep.json` mostra o envelope completo. O `source` distingue produtores:

| Componente | source | Endpoint |
|---|---|---|
| NoxusAgent Python | noxus-agent | POST /api/findings |
| **EXTENSÃO NOXUS VS CODE** | **noxus-vscode-extension** | **POST /api/integrations/noxus-vscode/scans** |

Em `.noxus/config.json`, cadastre `asset.consumed_apis`, por exemplo:

```json
[{"name":"Pagamentos","base_url":"https://api.exemplo.com","source":"manual"}]
```

Essa lista descreve APIs usadas pela aplicação; não há descoberta automática nesta versão. Campos desconhecidos ficam `null`. `asset.id` deve ser compartilhado entre Agent e extensão para o mesmo projeto. O nome do dev indica quem executou a análise, sem atribuir autoria do defeito.

`commands` permite apontar para ferramentas já instaladas usando **listas de argumentos**, por exemplo `"nikto": ["perl", "/caminho/nikto/program/nikto.pl"]`. Não são comandos de shell. `semgrep_config` aceita um ruleset, inicialmente `p/default`; regras locais podem ser usadas para evitar baixar regras em cada ambiente.

A API e a aplicação sob teste têm endereços distintos: `api_url` é o destino dos resultados; `asset.application_url` é o alvo do Nikto. Por padrão o alvo está limitado a loopback. A API não executa scans nem acessa URLs recebidas.

## Endpoints

Todos, exceto health e documentação, exigem `X-API-Key`.

| Método | Caminho | Função |
|---|---|---|
| GET | /health | Saúde e tipo de armazenamento |
| POST | /api/findings | Receber envelope normalizado |
| POST | /api/integrations/noxus-vscode/scans | Receber somente EXTENSÃO NOXUS |
| GET | /api/schema | JSON Schema do envelope |
| GET | /api/scans | Listar scans, inclusive vazios/com falha |
| GET | /api/scans/{uuid} | Envelope completo de uma execução |
| GET | /api/findings | Consultar, filtrar e paginar findings |
| PATCH | /api/findings/{id}/status | Triagem com responsável e motivo |
| GET | /api/findings/{id}/history | Histórico de triagem |
| GET | /api/assets | Ativos observados |
| GET | /api/dashboard | Contagens consolidadas |

Filtros de findings: `asset_id`, `source`, `tool`, `severity`, `status`, `limit`, `offset`. Paginação também em scans. Exemplos de status: `open`, `in_progress`, `resolved`, `false_positive`, `accepted_risk`.

Mesmo scan UUID + mesmo conteúdo retorna `replayed=true`. Mesmo UUID + conteúdo diferente retorna 409. O limite HTTP é 10 MiB e 20 mil findings/envelope. Os relatórios rejeitados por 409/413/422 ficam em `.noxus/agent/rejected/` para revisão, sem loop de reenvio. Fila usa tentativa a cada ciclo do monitor; no MVP local não há backoff exponencial.

A deduplicação conserva ocorrências do mesmo achado por ativo/repositório/branch/origem/ferramenta/regra/local/dependência. **Não correlaciona Semgrep com Sonar automaticamente.** Mudança de linha pode criar outro finding. Scan vazio não resolve achados anteriores automaticamente; triagem é preservada. IA, dashboard visual e extensão ficam para outros componentes.

## Arquivos e recuperação

- `.noxus/config.json`: configuração e chave local.
- `.noxus/agent/pending/*.json`: resultados ainda não confirmados pela API.
- `.noxus/agent/rejected/*.json`: resultados rejeitados permanentemente.
- `.noxus/dados/scans/*.json`: uma gravação atômica por execução, com horário de recebimento.
- `.noxus/dados/triage/*.json`: histórico por finding.

Gravação usa arquivo temporário + fsync + rename e lock do sistema operacional. Reiniciar a API mantém os dados. As consultas agregam JSONs sob demanda: adequado para volume pequeno local. Não edite arquivos enquanto processos estão ativos; faça backup da pasta `.noxus/`. Um arquivo corrompido gera erro em vez de ser ignorado silenciosamente.

Gitleaks não transmite valores de segredo nos campos conhecidos. Isso não é um detector universal de segredos em textos livres ou nomes de arquivo. A futura extensão deve igualmente limitar/sanitizar conteúdo antes do envio.

## Revisão e migração

Leia `docs/EXTENSAO-NOXUS.md` para implementar o futuro fork. O helper TypeScript não é uma extensão pronta. `docs/ARQUITETURA.md` descreve os módulos. `VALIDACAO.md` diferencia testes executados de integrações ainda não validadas.

Esta v2 é um pacote separado, preservando a entrega v1. O novo envelope aninhado substitui a entrada bruta/plana anterior. Não há importador do banco v1 nesta versão. A migração futura para PostgreSQL deve implementar uma camada equivalente a `JsonStore`, mantendo o contrato HTTP atual.

Testes:

```bash
python -m pip install -e '.[test]'
python -m pytest -q
```

## Referências oficiais usadas nos adaptadores

- https://semgrep.dev/docs/cli-reference
- https://github.com/gitleaks/gitleaks
- https://dependency-check.github.io/DependencyCheck/dependency-check-cli/arguments.html
- https://github.com/sullo/nikto/wiki/Export-Formats

A cobertura das linguagens/ecossistemas depende do scanner instalado. Dependency-Check não garante cobertura completa de todo gerenciador de pacotes; mensagens de erro e documentação do scanner devem ser consideradas.
