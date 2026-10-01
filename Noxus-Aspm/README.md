# Noxus ASPM

Aplicação local para cadastrar ativos, importar achados de segurança em JSON e
executar a triagem do Challenge3 com CrewAI. O dashboard inicia vazio.
Não há banco de dados nem carregamento automático de exemplos.

## Executar no Windows

Na raiz de Noxus-Aspm, a primeira instalação é:

```powershell
bun run setup:local
```

O comando aceita `bun run setup:local "C:/caminho/python.exe"` (Python 3.12 ou 3.13).
Ele usa `backend/.venv-local`, separado dos ambientes antigos copiados de outros PCs.
As dependências já foram instaladas neste computador durante a integração.

Primeiro terminal:

```powershell
bun run dev:api
```

Segundo terminal, também na raiz:

```powershell
bun run dev
```

Dashboard: http://localhost:3000

API/health: http://127.0.0.1:8000/api/health

Swagger: http://127.0.0.1:8000/docs

Mantenha os dois terminais abertos. A porta 8000 serve a API, não o dashboard.
Por padrão, o frontend usa http://127.0.0.1:8000/api; uma URL diferente pode ser
configurada em `.env.local` com `VITE_NOXUS_API_URL`. Não há modo mock.

## Usar o fluxo

1. Em Vulnerabilidades, selecione o envelope NOXUS 1.0 emitido pelo Agent ou extensão.
2. Clique em Importar JSON. O ativo é identificado pelo `asset.id` do envelope.
3. Revise os dados de negócio em Aplicações e ativos; não inferimos dono ou exposição.
4. Clique em Analisar pendentes. Até 50 pendentes são processados por vez.
5. Acompanhe a etapa e o resultado da execução.
6. Filtre por pendentes, prováveis verdadeiros positivos, possíveis falsos positivos
   ou inconclusivos. Clique no achado para ver a justificativa, confiança e JSON original.

Os resultados são sugestões da IA, não decisões humanas nem probabilidades calibradas.
Possíveis falsos positivos não são apagados, resolvidos ou escondidos por padrão.
Risco contextual, compliance e métricas de bloqueio não são inventados.

## Formato de importação

O formato correto é o envelope por varredura: `schema_version: "1.0"`,
`source`, `developer`, `asset`, `scan` e `findings`.
Não use o antigo JSON plano do Challenge3: a adaptação para a IA é interna.

- `source` identifica `noxus-agent` ou `noxus-vscode-extension`; não é SAST/DAST.
- Ferramenta e categoria vêm de `scan.tool` e `scan.category`.
- Cada finding tem `title`, `rule_id`, `location` e os campos opcionais do contrato.
  Não precisa ter `id` nem `tool` próprios.
- Severidade: `critical`, `high`, `medium`, `low`, `info` ou `null`, sem estimativa.
- CWE/CVE são listas. Linha e coluna começam em 1. URLs não podem conter credenciais,
  query ou fragmento. Datas da varredura precisam de fuso horário.
- Até 20.000 achados e 10 MiB por requisição. `findings: []` também registra a varredura.
- Reenvio do mesmo `scan.id` e conteúdo retorna `replayed: true`. Conteúdo diferente
  com o mesmo UUID retorna 409. Gere um UUID novo para cada execução, não para o retry.
- Repetições do mesmo achado são deduplicadas por ativo/repositório/branch,
  produtor/ferramenta, regra, localização e dependência. Scanners distintos não são unidos.
- Uma nova varredura pode atualizar o achado; a evidência anterior continua no arquivo
  da varredura. A nova evidência aguarda nova triagem. Scan vazio não resolve achados antigos.
- Título, descrição e recomendação de `SECRET` são sanitizados antes de gravar ou
  enviar à IA. Campos extras como `Secret`, `Match` ou `snippet` são rejeitados.
- O Agent deve normalizar os relatórios brutos. Não envie código ou credenciais.

Veja [o contrato e exemplo completo](backend/docs/CONTRATO_IMPORTACAO.md).
O histórico em **Varreduras recebidas** mostra inclusive scans vazios, parciais e falhos.

### Receber diretamente do Agent

O launcher do Agent já está integrado ao backend. Reinicie `bun run dev:api` após
esta atualização. Não execute `python -m noxus serve`: o receptor é a API do dashboard.

Na raiz do Noxus, faça o cadastro inicial (interativo, sem executar scans):

```powershell
bun run agent:init
```

Informe o repositório local que deseja analisar e os dados reais do executor/ativo.
A configuração fica em `backend/.data/noxus-agent/config.json`. Uma chave aleatória
compartilhada é criada em `backend/.data/agent-connection.json`, ignorada pelo Git.
Se `NOXUS_INGESTION_API_KEY` estiver no `backend/.env`, ela tem prioridade nos dois lados.
Não coloque chaves em variáveis `VITE_` nem no navegador.

Com os scanners já instalados, escolha uma ação em outro terminal:

```powershell
bun run agent:scan --tools semgrep gitleaks
# ou monitoramento contínuo (Ctrl+C encerra):
bun run agent:watch
# reenviar somente a fila pendente, sem novo scan:
bun run agent:flush
```

O Agent envia a `POST http://127.0.0.1:8000/api/findings`, com `X-API-Key` compartilhada.
Os resultados aparecem no dashboard; scans vazios/parciais/falhos ficam no histórico.
O CrewAI continua manual: clique em **Analisar pendentes** quando desejar triagem.
API indisponível mantém a fila. Rejeições 409/413/422 são preservadas em `rejected`.
`bun run agent:doctor` apenas consulta os executáveis disponíveis, não instala ferramentas.
Esta integração não instala nem garante disponibilidade dos scanners Windows/WSL.
Não executei novos testes, scans ou chamadas à IA nesta etapa, conforme solicitado.

Para usar um cadastro existente sem sobrescrevê-lo:

```powershell
bun run agent scan --config "C:/caminho/.noxus/config.json" --tools semgrep
```

O launcher mantém os dados e a fila desse cadastro e substitui destino/chave apenas
em memória. `NOXUS_API_KEY` herdada do terminal não desvia a chave compartilhada.
Altere `NOXUS_AGENT_PROJECT` no backend/.env caso mova o projeto irmão.
`NOXUS_AGENT_API_URL` permite outra porta local; configure também o servidor nessa porta.
Ele deve ser uma origem, como `http://127.0.0.1:8000`, **sem /api**.

A rota dedicada à extensão é `POST /api/integrations/noxus-vscode/scans`.
Antes do cadastro/chave explícita, as rotas de ingestão retornam 503.
`GET /api/schema`, com a chave, retorna o JSON Schema validável.

O upload local do dashboard usa `POST /api/v1/imports` com o mesmo contrato, sem
colocar uma chave no navegador. A API continua destinada a uso individual em localhost.
O código do Agent é carregado de `../NOXUS-Agent-API-v2/noxus-local-v2`, usando
o Python do backend. Seu servidor separado e seus relatórios antigos não são iniciados
nem importados automaticamente. O launcher não oferece o comando `demo`.

O arquivo histórico `challenge3/challenge3/input/vulnerabilities.json` é um
exemplo antigo: não é importado automaticamente nem deve ser apresentado como scan real.

## Onde os dados ficam

```text
backend/.data/
├── noxus.local.json       # ativos, originais, classificação atual e execuções
├── scans/<scan-id>.json   # um envelope validado/sanitizado por varredura
├── agent-connection.json # chave local compartilhada (não versionar)
├── noxus-agent/          # cadastro e filas pending/rejected do Agent
└── runs/<id>/
    ├── input.json        # snapshot do lote enviado aos agentes
    ├── progress.json     # última etapa iniciada
    └── output.json       # decisões, provedor, modelos e originais
```

Arquivos reais e credenciais são ignorados pelo Git. O antigo `noxus.dev.json`
fica preservado, mas não é usado pelo painel. O localStorage antigo também não
é lido. A pasta contexto não foi alterada.

O armazenamento tem escrita atômica, bloqueio de concorrência e um processo
por arquivo. Não use vários workers. Execuções interrompidas por reinício ficam
marcadas como interrompidas, sem fabricar resultados ou retomá-las silenciosamente.

## CrewAI e modelos

A ponte fica em `../challenge3/challenge3/noxus_bridge.py`.
O backend inicia esse arquivo com seu próprio Python e parâmetros de entrada/saída.
A cópia em `backend/crew_bridge` mantém o código de integração versionado.

O projeto existente usa OpenRouter. A aplicação e os JSON ficam locais, mas
com OpenRouter os achados do lote são enviados ao provedor ao clicar em Analisar.
Para inferência também no PC, configure Ollama em `challenge3/challenge3/.env.noxus`.
Veja [o guia de integração](backend/docs/INTEGRACAO_CREWAI_CHATBOT.md).

O pacote CrewAI traz dependências de bancos, mas este fluxo não as utiliza:
as tarefas são executadas diretamente, sem memória, RAG ou persistência de Crew.kickoff.
O histórico da aplicação é exclusivamente JSON.

## Recursos temporários do protótipo

O botão **Limpar dados** no Cérebro Central pede confirmação e remove os relatórios
recebidos, os achados revisados ou pendentes e o histórico/arquivos das análises.
Mantém o cadastro dos ativos e do Agent. A API bloqueia a limpeza enquanto uma
análise estiver em andamento e fora dos ambientes `development`/`test`.
Um Agent em `watch` pode enviar novos relatórios depois da limpeza; pare-o com Ctrl+C
se quiser manter o painel vazio. A limpeza não pode ser desfeita.

O inventário distingue **Encontrado automaticamente** de **Adicionado manualmente**.
Salvar a configuração de um ativo pendente confirma a revisão, mantendo sua origem.

## Extensão de IDE

O código-fonte incorporado fica em `extensions/noxus-ide`, com a identidade
**Noxus Extension for IDE**. Consulte o [guia do fork](extensions/noxus-ide/README_NOXUS.md).
Na raiz, `bun run ide:setup`, `bun run ide:prepare` e `bun run ide:build` preparam
a extensão. Depois escolha **Noxus Extension for IDE** na configuração F5 do VS Code.
A publicação dos resultados espera 10 segundos sem edição. O envio à API continua
preparado para a próxima etapa, conforme o escopo de apenas adicionar a extensão.

## Renomear ou mover a pasta

O nome atual é `Noxus-Aspm`. Scripts calculam os caminhos a partir da própria
localização, incluindo os projetos irmãos. Após mover/renomear, feche os processos
antigos, reabra o VS Code na nova pasta e execute `bun run setup:local` para atualizar
os launchers Python e a instalação editável. Configurações externas com caminhos
absolutos (`NOXUS_*_PROJECT`, `NOXUS_DATA_FILE` e o `project_path` do cadastro do Agent)
devem apontar para os diretórios atuais. IDs de ativos, URLs de repositórios e
evidências históricas não são nomes de pasta e não são reescritos.

Neste checkout, o Git da pasta `Challenge` ainda registra `Noxus-Aspm360` como
gitlink (entrada de submódulo), sem `.gitmodules`. Por isso a renomeação aparece
como a remoção dessa entrada e a nova pasta `Noxus-Aspm/` não rastreada.
Os arquivos foram mantidos; esta etapa não altera o índice nem cria commits.
Antes de versionar, regularize essa estrutura no repositório pai conforme a forma
escolhida pela equipe (pasta comum ou submódulo).

## Verificações locais

```powershell
bun run typecheck
bun run lint
bun run build
cd backend
.\.venv-local\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.test-results
.\.venv-local\Scripts\python.exe -m ruff check app tests crew_bridge
```

Os testes usam diretórios temporários. Há teste do protocolo entre processos
e teste com agentes/tarefas reais do CrewAI e um LLM controlado, sem chamadas
externas. Eles não comprovam a qualidade ou disponibilidade dos modelos externos.

Stack: React, TypeScript, TanStack Router/Query/Start, Vite, Tailwind e FastAPI.
Chatbot, descoberta automática e Risk Engine continuam fora deste fluxo.
Scanners são executados somente pelo Agent, após comando explícito do usuário.
Há chave para ingestão externa; as telas e rotas locais não possuem
login nem multi-tenancy. Não exponha este servidor à internet.
