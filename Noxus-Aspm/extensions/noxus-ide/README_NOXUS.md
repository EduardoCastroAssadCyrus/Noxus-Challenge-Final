# Noxus Extension for IDE

Fork local do código SonarQube for IDE / SonarLint fornecido na pasta
`Challenge/sonarlint-vscode-master/sonarlint-vscode-master`. Licença, NOTICE,
créditos e README originais permanecem nesta pasta. Não é uma publicação oficial da SonarSource.

Identidade VS Code: `noxus.noxus-vscode-extension`. Os comandos, configurações e
mensagens do protocolo continuam com os identificadores Sonar para compatibilidade
com o servidor de linguagem original. Desative a extensão Sonar oficial ao executar
este fork, pois ambas registram esses mesmos comandos.
A telemetria herdada do fornecedor fica desativada por padrão neste fork local.

## Escopo desta etapa

Código incorporado ao projeto, identidade Noxus e publicação dos diagnósticos,
hotspots, taint e riscos de dependências após **10 segundos sem editar nenhum arquivo**.
Cada nova edição reinicia a espera; o último resultado substitui o anterior na fila.
O protocolo de sincronização com os analisadores continua ativo para não perder edições.
Fechar o documento ou desativar a extensão cancela as publicações pendentes.

Conforme o escopo de apenas incorporar a extensão, ainda não há cadastro Noxus,
emissão de JSON ou envio HTTP automático ao dashboard. Não há novas funções de scanner.
O ponto preparado para o envio fica em `src/extension.ts`, dentro da publicação
adiada de `handleDiagnostics`. A espera comum fica em `src/noxus/idleReports.ts`.

## Executar em desenvolvimento

Na raiz `Noxus-Aspm`, use um Node compatível com as dependências do fork:

```powershell
bun run ide:setup
bun run ide:prepare
bun run ide:build
```

No VS Code, escolha **Noxus Extension for IDE** em Executar e Depurar e pressione F5.
Essa configuração usa caminhos relativos e acompanha futuras mudanças do nome da pasta.

Se preferir abrir somente a pasta `extensions/noxus-ide`, os comandos equivalentes são:

```powershell
npm ci --ignore-scripts
npm run prepare
npm run webpack
```

Nessa pasta, pressione F5 (Launch Extension). O `prepare` original baixa o servidor Java
e analisadores; downloads e disponibilidade dependem do fornecedor. O analisador
OmniSharp marcado `requiresCredentials` é ignorado quando não há credenciais.
Configure Java 21 ou superior em `sonarlint.ls.javaHome` se necessário.
Esta cópia de código não inclui os binários Java nem um VSIX já instalado.
As dependências npm e o build TypeScript foram verificados nesta integração; a sessão
de análise dentro do VS Code depende desses binários e não foi executada aqui.

Teste isolado da espera, sem scanners, downloads ou IA (na raiz Noxus-Aspm):

```powershell
bun test extensions/noxus-ide/test/noxus/idleReports.test.ts
```

Também disponível na raiz como `bun run ide:test`.

## Contrato preparado para a próxima integração

Receptor existente: `POST http://127.0.0.1:8000/api/integrations/noxus-vscode/scans`.
Usar `X-API-Key` em armazenamento seguro do VS Code, nunca no código ou em configurações
versionadas. O envelope NOXUS 1.0 deve declarar `source: noxus-vscode-extension`,
`scan.tool: sonar`, `scan.category: SAST`, executor e ativo reais, e UUID por varredura.
Consulte `../../backend/docs/CONTRATO_IMPORTACAO.md`; `/api/schema` expõe o schema.
O futuro adaptador deve normalizar somente diagnósticos recebidos, preservar o mesmo
UUID em retries, descartar resultados de versões antigas e não transmitir código/segredos.
