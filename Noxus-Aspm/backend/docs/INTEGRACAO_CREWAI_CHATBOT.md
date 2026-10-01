# Integração local: Noxus e Challenge3

## Caminho implementado

```text
Envelope NOXUS 1.0 → validação/sanitização → scans/<id>.json + noxus.local.json
  → execução solicitada
  → runs/<id>/input.json → Challenge3/noxus_bridge.py
  → quatro tarefas CrewAI → output.json validado
  → classificação no JSON principal → dashboard atualizado
```

O processo da IA usa o mesmo Python do backend, separado em subprocesso.
O frontend envia o envelope completo, sem extrair findings. O backend gera IDs
estáveis para o painel e adapta cada achado para `{id, original}` na entrada da ponte.
`original` contém schema_version, source, developer, asset, scan e o finding individual.
Campos omitidos recebem somente os defaults do contrato; severidade null permanece null.
O contrato enviado aos agentes esclarece que developer não é autoria da falha e
que SECRET já foi sanitizado. Não há envio de Secret, Match, snippets ou relatório bruto.
A ponte existente aceita este original estruturado; não precisa de outro parser no Challenge3.
Uma nova varredura durante a análise invalida a aplicação da resposta antiga ao achado atualizado.
O caminho padrão é a pasta irmã `challenge3/challenge3`.
Para outro local, configure `NOXUS_CREW_PROJECT` com caminho absoluto no backend.
O timeout padrão é 600 segundos (`NOXUS_CREW_TIMEOUT_SECONDS`).

## Provedor e modelos

O Challenge3 lê seu próprio `.env`, seguido de `.env.noxus` para ajustes desta
integração. O navegador não recebe credenciais.

OpenRouter (compatível com a configuração original):

```dotenv
NOXUS_LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=
# Opcional: substitui os modelos individuais de config/agents.yaml.
# NOXUS_LLM_MODEL=provedor/modelo
```

Esse modo faz chamadas externas e envia os achados escolhidos ao provedor.
Um status ready comprova configuração local, não validade da chave, saldo,
disponibilidade do modelo ou qualidade da análise.

Para modelo também local, com um modelo já instalado no Ollama:

```dotenv
NOXUS_LLM_PROVIDER=ollama
NOXUS_LLM_MODEL=nome-do-modelo-instalado
OLLAMA_BASE_URL=http://localhost:11434
```

Nenhum modelo é baixado automaticamente. Os nomes dos modelos OpenRouter
originais são preservados em config/agents.yaml; não assumimos que estarão
sempre disponíveis. Altere a configuração quando necessário.

## Responsabilidades dos agentes

1. vulnerability_analyzer: analisa as evidências fornecidas.
2. fp_tp_validator: questiona hipóteses e identifica informação insuficiente.
3. security_classifier: sugere classificação.
4. json_validator: retorna decisions estruturadas para todos os IDs.

As tarefas locais são definidas na ponte; os papéis e modelos vêm do YAML.
A ausência de evidência pode resultar em inconclusive. Valores de confiança
são estimativas do modelo, não métricas calibradas.

A ponte usa Task.execute_sync e output_pydantic. Não usa Crew.kickoff,
memória ou bancos internos. Documentação de referência:
[Tasks do CrewAI](https://docs.crewai.com/en/concepts/tasks).

Depois da IA, validações determinísticas verificam IDs, unicidade, quantidade,
faixa de confiança e preservação dos originais. O backend repete a validação.
Qualquer erro rejeita toda a saída daquela execução.

## Arquivos e manutenção

A versão da ponte em `backend/crew_bridge/` é copiada para Challenge3.
Ao modificar a ponte, mantenha as duas versões alinhadas.
`main.py` agora exige caminhos explícitos; não carrega input/vulnerabilities.json sozinho.
As entradas antigas de main.py/content_crew.py foram guardadas em .noxus-backup/.

Não é necessário iniciar um servidor separado para CrewAI.
Abra o dashboard e solicite a análise. Os modelos só são chamados nessa ação.
O teste automatizado usa um LLM controlado e não envia relatórios à internet.

## Chatbot

Permanece desabilitado, sem respostas simuladas.
O ponto futuro é `app/ai/chatbot/service.py`, usando um ChatProvider
configurado em `app/main.py`. Ele poderá consultar findings e análises armazenadas
no JSON; não é necessário criar um banco para isso.
