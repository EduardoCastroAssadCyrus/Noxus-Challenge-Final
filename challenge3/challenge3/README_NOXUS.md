# Challenge3 integrado ao Noxus

O Noxus inicia `noxus_bridge.py` automaticamente quando você solicita uma análise
em Vulnerabilidades ou Equipe Agêntica. Nenhum arquivo de exemplo é carregado.
O backend usa o próprio Python, com as dependências CrewAI instaladas.
O antigo `.venv` copiado de outro PC não participa deste fluxo.

Os quatro agentes definidos em `config/agents.yaml` são usados em sequência:
análise, revisão, classificação e validação. A ponte permite também inconclusivos.
Os prompts antigos de `config/tasks.yaml` pertencem ao protótipo independente;
a ponte define tarefas próprias com saída estruturada e validação de IDs.

Não usamos Crew.kickoff, memória, embeddings nem banco de dados: as tarefas CrewAI
são executadas diretamente, e os históricos ficam em JSON no backend.

## Modelo

A ponte lê primeiro `.env` e depois `.env.noxus`. Não versione esses arquivos.
Com OpenRouter, os relatórios são enviados ao provedor configurado; somente os
arquivos e a aplicação ficam locais. O clique em Analisar inicia essas chamadas.

Para preservar os modelos de `config/agents.yaml`:

```dotenv
NOXUS_LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=
```

Para escolher um único modelo, acrescente `NOXUS_LLM_MODEL=provedor/modelo`.
Disponibilidade dos modelos depende da sua conta e do provedor.

Para inferência também local, instale um modelo no Ollama e configure:

```dotenv
NOXUS_LLM_PROVIDER=ollama
NOXUS_LLM_MODEL=nome-do-modelo-instalado
OLLAMA_BASE_URL=http://localhost:11434
```

Confira a configuração sem enviar dados para IA:

```powershell
& "../../Noxus-Aspm360/backend/.venv-local/Scripts/python.exe" main.py --check
```

Entrada da ponte: `{"findings": [{"id": "ID interno", "original": {...}}]}`.
Saída: `decisions`, provedor, modelos e originais preservados.
O backend valida a saída de novo antes de publicá-la no dashboard.

Os arquivos antigos em input/output são exemplos históricos: não são importados
automaticamente. main.py agora exige os caminhos de entrada/saída explicitamente.
As versões anteriores de main.py e content_crew.py foram preservadas em .noxus-backup/.
