# Backend Noxus ASPM

API local FastAPI com persistência exclusivamente JSON. O estado inicial é vazio.
As instruções de instalação e execução estão no [README principal](../README.md).

## Endpoints

| Operação | Endpoint |
|---|---|
| Saúde | GET /api/health |
| Dashboard calculado | GET /api/v1/dashboard |
| Listar/cadastrar ativos | GET/POST /api/v1/assets |
| Configurar ativo | PATCH /api/v1/assets/{id} |
| Importar relatório normalizado | POST /api/v1/imports |
| Histórico de varreduras, incluindo vazias/falhas | GET /api/v1/scans |
| Receber do Agent (X-API-Key) | POST /api/findings |
| Receber da extensão (X-API-Key) | POST /api/integrations/noxus-vscode/scans |
| Schema NOXUS 1.0 (X-API-Key) | GET /api/schema |
| Listar/detalhar achados | GET /api/v1/findings e /api/v1/findings/{id} |
| Configuração do CrewAI | GET /api/v1/analysis/status |
| Iniciar análise | POST /api/v1/analysis/runs |
| Histórico de análises | GET /api/v1/analysis/runs |
| Limpar relatórios do protótipo | POST /api/v1/reports/clear |

A limpeza exige `{"confirmation": "LIMPAR DADOS"}`, ambiente development/test e
nenhuma análise em execução. Remove achados, scans e análises, mantendo cadastros.

POST /analysis/runs aceita `{"findingIds": []}`: uma lista vazia seleciona até
50 achados ainda não analisados. IDs explícitos permitem reanálise.
Uma execução por vez. O retorno 202 informa o ID; consulte o histórico
até completed/failed/interrupted. Cada rodada mantém seus próprios arquivos.

O upload e as rotas de ingestão recebem o envelope NOXUS 1.0 completo, não o
formato plano antigo. [Contrato](docs/CONTRATO_IMPORTACAO.md).
Importações idênticas são idempotentes por scan.id. Conflitos de UUID rejeitam o lote.
Classificação não altera severidade técnica, evidência original ou status humano.
Falhas de IA não produzem resultados substitutos.

## Persistência

`app/repositories/json_repository.py` mantém ativos, findings e execuções.
`app/domain/scan_contract.py` valida o contrato NOXUS 1.0 e sanitiza SECRET.
`app/ingestion.py` adapta os dados para o dashboard e para a ponte Challenge3.
`app/ai/local_runner.py` coordena o subprocesso e valida a resposta.
A ponte salva arquivos em `.data/runs/<id>`; o estado fica em `.data/noxus.local.json`.
Cada varredura tem um registro em `.data/scans/<scan-id>.json`. O índice é recuperado
na inicialização se houver interrupção entre salvar o scan e atualizar o estado.

Um bloqueio de arquivo impede dois processos de usarem o mesmo armazenamento.
Arquivos inválidos causam erro: não são apagados ou recriados com exemplos.

A API usa Python 3.12/3.13. Neste PC, use `.venv-local` e execute
`bun run dev:api` na raiz do projeto. O ambiente `.venv` antigo não é necessário.
O `uv.lock` registra as dependências; para usar uv, selecione explicitamente
`UV_PROJECT_ENVIRONMENT=.venv-local` e o Python funcional.

Chatbot e asset discovery respondem 503 enquanto não configurados.
O servidor é para uso individual em localhost, com origens CORS explícitas.

## Agent conectado

`bun run agent:init`, na raiz, cadastra o projeto e cria a chave compartilhada.
`bun run agent:scan`, `agent:watch` e `agent:flush` reutilizam o projeto irmão
NOXUS-Agent-API-v2 com o Python deste backend e enviam diretamente para `/api/findings`.
Não inicie `noxus serve`. A chave gerada fica em `.data/agent-connection.json`;
`NOXUS_INGESTION_API_KEY` explícita tem prioridade. Nunca devolvemos a chave ao frontend.
O Agent usa JSONs de fila; o backend continua sendo o único escritor do inventário.
