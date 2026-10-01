# Importação NOXUS 1.0

Implementa o formato do guia `CONTRATO-JSON-API-FINDINGS.md`:
um envelope por varredura, normalizado pelo NoxusAgent ou futura extensão.
O dashboard não aceita o JSON bruto do scanner nem o antigo JSON plano do Challenge3.

## Exemplo sintético (somente documentação)

```json
{
  "schema_version": "1.0",
  "source": "noxus-agent",
  "developer": {"name": "Executor do teste", "role": "Dev", "team": "Back-End"},
  "asset": {
    "id": "backend-demo",
    "name": "Aplicação de exemplo",
    "type": "web-api",
    "repository_url": "https://github.com/exemplo/backend",
    "branch": "main",
    "commit": null,
    "local_ip": "127.0.0.1",
    "application_url": "http://localhost:8080",
    "consumed_apis": []
  },
  "scan": {
    "id": "a578af66-a49a-4913-909f-3dd1af647813",
    "tool": "semgrep",
    "tool_version": null,
    "category": "SAST",
    "started_at": "2026-10-01T10:00:00-03:00",
    "finished_at": "2026-10-01T10:00:05-03:00",
    "status": "completed",
    "trigger": "manual",
    "error": null
  },
  "findings": [{
    "title": "Achado sintético",
    "description": "Somente demonstração do formato.",
    "rule_id": "example.sql-injection",
    "severity": "high",
    "cwe": ["CWE-89"],
    "cve": [],
    "location": {"file": "src/database.py", "line": 42, "column": 8},
    "dependency": null,
    "recommendation": "Use consultas parametrizadas."
  }]
}
```

O exemplo não é carregado automaticamente. Use um UUID novo para cada scan real.
Para Sonar: `source: "noxus-vscode-extension"`, `scan.tool: "sonar"`,
`scan.category: "SAST"` e um novo `scan.id`.

## Regras

| Ferramenta | Categoria | Produtor |
|---|---|---|
| semgrep | SAST | noxus-agent |
| gitleaks | SECRET | noxus-agent (também permitido à extensão pelo schema) |
| dependency-check | SCA | noxus-agent |
| nikto | DAST | noxus-agent |
| sonar | SAST | noxus-vscode-extension |
| dependency-reputation | SCA | noxus-vscode-extension |
| extension-reputation | EXTENSION | noxus-vscode-extension |

- `scan.id`: UUID estável em tentativas de reenvio; novo por execução.
- `asset.id`: ID estável da mesma aplicação entre produtores. O inventário não
  correlaciona ativos automaticamente por nomes ou URLs parecidas.
- Datas com fuso, término igual ou posterior ao início.
- Status: `completed`, `partial`, `failed`. `failed` exige `error` e `findings: []`.
- Severidade: `critical`, `high`, `medium`, `low`, `info` ou `null`. Não converter
  desconhecida em baixa/informativa. Sem severidade informada, o default é null.
- `cwe` e `cve`: listas de identificadores válidos, não strings únicas.
- `location`: arquivo, URL ou objeto vazio quando houver `dependency`.
  Linha e coluna são inteiros positivos, não booleanos, e exigem arquivo.
- `dependency`: nome obrigatório, versão/ecossistema opcionais. Extensão usa
  `ecosystem: "vscode"` e nome no formato `publisher.extensao`.
- URLs HTTP(S), sem credenciais, query ou fragmento.
- `consumed_apis`: lista declarada de APIs usadas pela aplicação, não scanners consultados.
- `developer` identifica o executor, não a autoria da vulnerabilidade nem o dono do ativo.
- Campos desconhecidos são rejeitados. SECRET tem título, descrição e recomendação
  substituídos antes de persistência/IA. O cliente não deve enviar segredos em nenhum campo.
- Limites: 10 MiB por requisição (inclusive sem Content-Length), 20.000 findings.

## Rotas e respostas

O upload do dashboard usa `POST /api/v1/imports` (201) e envia o envelope completo.
Para CLI/Agent: `POST /api/findings` (200), com `X-API-Key` correspondente a
`NOXUS_INGESTION_API_KEY` do backend. Para a extensão:
`POST /api/integrations/noxus-vscode/scans` (200), mesma chave, somente seu produtor.
O JSON Schema atual pode ser consultado em `GET /api/schema` com essa chave.

```json
{
  "scan_id": "a578af66-a49a-4913-909f-3dd1af647813",
  "received": 1,
  "replayed": false,
  "created": 1,
  "updated": 0,
  "duplicates": 0
}
```

`created` conta novos achados agregados; `updated` conta achados atualizados por uma
nova varredura; `duplicates` conta repetições ignoradas no lote ou evidências mais
antigas. Reenvio idêntico tem `replayed: true`, zero criações/atualizações.
O digest do JSON recebido detecta diferenças mesmo em textos SECRET sanitizados,
sem guardar esses textos. Ordem das chaves e espaçamento JSON não mudam o digest.

409: UUID já recebido com conteúdo diferente. 422: JSON/contrato inválido;
respostas de validação não incluem os valores de entrada. 413: corpo acima do limite.
401: chave ausente/incorreta nas rotas do Agent/extensão. 503: chave não configurada.
`bun run agent:init` gera e compartilha a chave local com este backend. O launcher
`scripts/noxus_agent.py` conecta o Agent irmão sem iniciar sua API separada.
Uma `NOXUS_INGESTION_API_KEY` explícita tem prioridade sobre a chave gerada.

## Persistência e IA

`backend/.data/scans/<scan-id>.json` contém o envelope normalizado/sanitizado,
horário de recebimento e digest. Não contém o corpo bruto de SECRET.
`noxus.local.json` é o índice do painel. Um scan gravado antes de uma interrupção
é reaplicado ao índice na inicialização, uma única vez.

O histórico do scan permanece imutável. O agregado deduplica por ativo, repositório,
branch, produtor, ferramenta, regra, localização e dependência. Uma evidência mais
antiga não sobrescreve uma mais nova. Scan vazio não resolve vulnerabilidades.

Antes de iniciar o Challenge3, o backend monta `{id, original}` por achado.
`original` inclui todos os metadados do envelope e `finding` individual.
O resultado da IA não muda a severidade nem apaga evidências. Nova varredura exige
nova triagem; resultados de um snapshot antigo não sobrescrevem evidência atualizada.

O contrato Python fica em `app/domain/scan_contract.py`; qualquer mudança futura
deve ser coordenada com `NOXUS-Agent-API-v2/noxus-local-v2/noxus/models.py`.
O launcher reutiliza o Agent sem modificar o projeto irmão. Scanners são iniciados
somente por `agent:scan` ou `agent:watch`. Dados antigos da outra API não são importados
automaticamente. Consulte o README principal para execução integrada.
