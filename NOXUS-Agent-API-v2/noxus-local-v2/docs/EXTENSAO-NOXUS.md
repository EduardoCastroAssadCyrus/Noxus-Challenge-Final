# Contrato da futura EXTENSÃO NOXUS para VS Code

A extensão planejada é o fork modificado do SonarQube for IDE. **Ela não está implementada neste pacote.** A API, o contrato e o exemplo de envio estão implementados. Não presumimos acesso público a diagnostics de outra extensão; o futuro fork deve obter os resultados dentro do próprio pipeline de análise.

Identificadores obrigatórios:

- Constante Python: `NOXUS_VSCODE_EXTENSION_SOURCE` em `noxus/models.py`.
- Valor JSON: `"source": "noxus-vscode-extension"`.
- Rota dedicada: `POST /api/integrations/noxus-vscode/scans`.
- Handler Python: `receive_noxus_vscode_extension_scan` em `noxus/api.py`.
- Tag Swagger: `EXTENSÃO NOXUS VS CODE`.
- A rota comum `POST /api/findings` também aceita esse produtor.
- Autenticação: `X-API-Key`; configure a mesma chave da API no SecretStorage do VS Code.

`source` identifica a extensão. `scan.tool` identifica qual mecanismo produziu aquele relatório:

| tool | category | Uso |
|---|---|---|
| sonar | SAST | Inspeção de código do fork SonarQube for IDE |
| dependency-reputation | SCA | Verificação futura de bibliotecas/dependências |
| extension-reputation | EXTENSION | Verificação futura de extensões VS Code |
| gitleaks | SECRET | Caso o futuro fork integre Gitleaks |

Enviar um envelope por ferramenta e execução. `schema_version` é `1.0` do novo envelope, apesar da versão da API ser 2.0. Esse contrato **não é compatível** com o envelope plano da API v1 anterior.

Veja `examples/noxus-vscode-sonar.json`, `examples/noxus-vscode-dependency.json` e `examples/noxus-vscode-extension.json`. O JSON Schema completo está em `docs/scan-envelope.schema.json`; OpenAPI em `docs/openapi.json`.

## Regras para o Codex que implementará a extensão

1. Obter configuração do dev/ativo e compartilhar o mesmo `asset.id` do Agent para o mesmo projeto. O ID do ativo deve permanecer estável.
2. Cada execução recebe um UUID novo. Reenvios mantêm UUID **e conteúdo idênticos**. Nunca alterar timestamp para reenviar.
3. Converter posições do VS Code (base zero) para linhas e colunas base um.
4. Mapear severidade Sonar explicitamente. Não tratar automaticamente toda categoria de qualidade como vulnerabilidade de segurança. Enviar apenas regras selecionadas de segurança; severidade desconhecida = `null`.
5. Não enviar código-fonte, credenciais, snippets ou relatório Sonar bruto. Enviar campos permitidos pelo schema. Revisar também mensagens livres que possam conter valores sensíveis.
6. Guardar a fila durável usando `globalStorageUri`/`storageUri`. Usar retry com backoff para erro de conexão, 429 e 5xx. HTTP 401 exige corrigir a chave; 409 exige investigar colisão de UUID; 413 exige reduzir o relatório; 422 exige corrigir o contrato.
7. Usar debounce e eventos de salvamento. A extensão é responsável pelo agendamento; a API só recebe.
8. Um scan vazio concluído registra a execução, mas **não resolve automaticamente findings anteriores**. A API preserva triagem manual. Análises incrementais de um arquivo não são prova de correção no projeto inteiro.
9. `dependency` também representa uma extensão: use `name="publisher.extension"`, `version` e `ecosystem="vscode"` com categoria EXTENSION.
10. `consumed_apis` é contexto da aplicação; não é lista de serviços consultados pelo scanner. Cadastro manual no MVP.

`examples/extension-client.ts` é somente um auxiliar HTTP revisável, não uma extensão pronta. Não adiciona dependências Sonar nem implementa captura de diagnostics. O desenvolvedor futuro deve implementar fila, mapeamento e eventos conforme acima.
