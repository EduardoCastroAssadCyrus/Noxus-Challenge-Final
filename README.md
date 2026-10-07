# Noxus ASPM — guia geral de instalação e operação

Guia do conjunto de projetos da pasta **Challenge**, revisado em 01/10/2026.
Os comandos abaixo correspondem ao código existente nesta entrega.

## 0. Participantes
Eduardo Castro Assad RM.571577
Gabriel Eduardo Pante RM.569540
Artur Nogueira Francisco RM.570143

## 1. O que o projeto faz

O Noxus ASPM centraliza achados de segurança, relaciona os relatórios aos ativos cadastrados e oferece triagem assistida por IA. Atualmente é apenas um MVP, com uso atual sendo individual, no próprio computador, com persistência em arquivos JSON.

```text
Código/aplicação local
  → NoxusAgent → Semgrep / Gitleaks / Dependency-Check / Nikto
  → API FastAPI → arquivos JSON → dashboard React
  → botão "Analisar pendentes" → Challenge3/CrewAI → resultados no dashboard
```

| Componente | Situação nesta entrega |
|---|---|
| Dashboard, inventário, importação e histórico | Implementados |
| Cadastro do desenvolvedor/projeto pelo terminal | Implementado no Agent |
| Execução e envio dos quatro scanners | Implementados; exigem instalação das ferramentas e alvo disponível |
| Triagem dos findings pelo CrewAI | Implementada; exige configuração do provedor/modelo |
| Noxus Extension for IDE | Código incorporado e compilável; alertas aguardam 10 segundos sem edição |
| Envio de relatórios da extensão ao ASPM | Ainda não implementado; receptor e ponto de integração preparados |
| Chatbot | Desabilitado; integração futura |
| Descoberta por IA de APIs desconhecidas | Ainda não implementada; ativos recebidos por relatório entram automaticamente no inventário |
| Login, contas, organização e múltiplos clientes | Não implementados neste protótipo local |

**"Cadastro" aqui significa informar desenvolvedor, equipe e projeto ao Agent. Não existe tela de criar conta, senha ou login no dashboard.**

Não é necessário instalar PostgreSQL, MySQL, SQLite, Docker ou um servidor SonarQube para o fluxo descrito. O Dependency-Check mantém seu próprio cache de vulnerabilidades; isso não é o armazenamento do ASPM. OpenRouter faz inferência externa; para manter também a inferência no PC, use a opção Ollama.

## 2. Pastas e qual guia seguir

```text
Challenge/
├── README.md                              ← este guia
├── Noxus-Aspm/                            ← raiz do dashboard e backend
│   ├── package.json
│   ├── scripts/noxus_agent.py
│   ├── backend/
│   └── extensions/noxus-ide/               ← fork Noxus da extensão
├── NOXUS-Agent-API-v2/noxus-local-v2/       ← implementação dos scanners/Agent
├── challenge3/challenge3/                 ← ponte CrewAI e configuração dos modelos
└── sonarlint-vscode-master/               ← fonte original; não é o fork integrado
```

Preserve os nomes e a relação entre essas pastas. Linux diferencia maiúsculas de minúsculas: `challenge3/challenge3` deve existir exatamente assim.

| Seu ambiente | Caminho neste documento |
|---|---|
| Windows, com os quatro scanners | [Windows completo via WSL2](#4-windows--fluxo-completo-com-wsl2) |
| Linux | [Linux Ubuntu 24.04](#5-linux--ubuntu-2404) |
| Windows nativo, apenas painel/API/cadastro/IA | [Alternativa Windows nativo](#6-windows-nativo--painel-api-e-cadastro) |

O instalador `noxus install-tools` **recusa Windows nativo**. Por isso o fluxo completo Windows deste guia usa Ubuntu no WSL2, com API, Agent, scanners e ferramentas dentro do mesmo Linux. Não misture o Python do Windows com os binários dos scanners do WSL.

Os READMEs antigos do Agent também descrevem uma API independente. **Para o fluxo integrado deste guia, não execute `noxus serve` nem `noxus demo`.** O receptor é sempre o backend de `Noxus-Aspm`.

## 3. Dependências necessárias

O arquivo [requirements.txt](requirements.txt) centraliza a instalação Python e o inventário das demais dependências, com os comandos para frontend, extensão e scanners. Execute seus comandos a partir de `Challenge`.

### 3.1 Instalações do sistema

| Dependência | Uso | Instalação coberta |
|---|---|---|
| Ubuntu 24.04, x86_64 ou ARM64 | Base dos comandos Linux e do instalador de scanners | Nativo ou WSL2 |
| Python 3.12 ou 3.13, pip e venv | API, Agent e CrewAI; Python 3.14 não está aceito pelo backend | apt no Linux; winget no Windows nativo |
| Bun 1.4.x | Dependências, scripts e dashboard | Instalador oficial |
| Node.js 24 + npm | Vite/ferramentas JS e build da extensão | nvm no Linux; winget no Windows |
| Git | Metadados do repositório e download do Nikto | apt/winget |
| Java 21 | Dependency-Check e servidor da extensão | OpenJDK no Linux; Temurin no Windows |
| Perl + módulos SSL/HTTP | Nikto | apt |
| curl, certificados CA, unzip, tar e rsync | Downloads, extração e preparação do ambiente Linux | apt |
| build-essential, Python headers, libffi/libssl e pkg-config | Suporte à instalação de dependências Python com extensões nativas | apt |
| Semgrep | SAST | Instalador do Agent, no ambiente separado dos scanners |
| Gitleaks | Secret scanning | Instalador do Agent |
| OWASP Dependency-Check CLI | SCA/dependências | Instalador do Agent |
| Nikto | DAST de uma aplicação local em execução | Instalador do Agent |
| Navegador | Dashboard | Navegador já instalado no PC |
| VS Code >= 1.100 | Somente para desenvolver/executar a extensão | Opcional |
| Ollama + um modelo baixado | Somente para triagem com inferência local | Opcional; seção 8 |
| Conta/chave OpenRouter + modelo disponível | Somente para triagem pelo OpenRouter | Alternativa ao Ollama; seção 8 |
| Chave NVD | Ajuda a atualizar o catálogo do Dependency-Check sem limites tão restritos | Opcional; seção 9 |

Instale também as dependências **do projeto que será analisado**, conforme o README dele. O ASPM não instala nem inicia automaticamente a aplicação do cliente.

Todas as bibliotecas diretas do ASPM, Agent e extensão estão no [apêndice de dependências](#13-inventario-completo-de-dependencias-diretas). Os comandos de instalação resolvem também as dependências transitivas; não instale cada biblioteca manualmente.

### 3.2 Preparação sem misturar ambientes

Este guia usa:

- `backend/.venv-local` para API e CrewAI.
- `backend/.data/noxus-agent/scanners-venv` para o instalador/CLI dos scanners.
- `backend/.data/noxus-agent/config.json` como **único cadastro compartilhado**.
- `backend/.data/noxus-agent/tools` para os scanners baixados.

Semgrep fica fora do ambiente CrewAI para evitar que dependências de uma ferramenta alterem as da outra. A integração usa os executáveis registrados no mesmo `config.json`.

## 4. Windows — fluxo completo com WSL2

### W1. Instalar Ubuntu no WSL

**Terminal: PowerShell como administrador.**

```powershell
wsl --install -d Ubuntu-24.04
```

Reinicie o computador se solicitado. Abra **Ubuntu-24.04** e crie o usuário/senha do Linux. Esse usuário é do sistema operacional, não é o cadastro do ASPM. A instalação é descrita pela [Microsoft](https://learn.microsoft.com/en-us/windows/wsl/install).

**Terminal: PowerShell comum, após a instalação.**

```powershell
wsl --list --verbose
wsl -d Ubuntu-24.04
```

A distribuição deve aparecer com VERSION 2. Se aparecer 1, saia do Ubuntu com `exit` e execute `wsl --set-version Ubuntu-24.04 2` no PowerShell.

**A partir de W2, todos os comandos desta seção são executados no terminal Ubuntu/Bash, não no PowerShell.**

### W2. Instalar as ferramentas básicas no Ubuntu

```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip \
  git curl ca-certificates unzip tar rsync nano build-essential pkg-config \
  libffi-dev libssl-dev perl libnet-ssleay-perl libio-socket-ssl-perl \
  libwww-perl openjdk-21-jdk-headless

curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.8/install.sh | bash
export NVM_DIR="$HOME/.nvm"
. "$NVM_DIR/nvm.sh"
nvm install 24
nvm alias default 24
nvm use 24

curl -fsSL https://bun.com/install | bash
export PATH="$HOME/.bun/bin:$PATH"

python3.12 --version
node --version
npm --version
bun --version
java -version
git --version
perl -v
```

Os instaladores de [nvm](https://github.com/nvm-sh/nvm#installing-and-updating) e [Bun](https://bun.sh/docs/installation) são os oficiais. Os exports acima habilitam as ferramentas no terminal atual; os instaladores também configuram os próximos terminais Bash.

### W3. Preparar uma cópia Linux limpa do conjunto Challenge

Encerre com Ctrl+C os servidores Noxus que estiverem rodando no Windows. Não execute as duas instalações simultaneamente nas mesmas portas.

A linha `NOXUS_SOURCE` abaixo corresponde à localização deste checkout. Se seu Windows usa outro caminho, altere **somente essa linha**. `C:\...` vira `/mnt/c/...` no WSL.

```bash
NOXUS_SOURCE="/mnt/c/Users/jacki/Documents/Faculdade e tals/Challenge"
test -f "$NOXUS_SOURCE/Noxus-Aspm/package.json"
test -f "$NOXUS_SOURCE/NOXUS-Agent-API-v2/noxus-local-v2/noxus/agent.py"
test -f "$NOXUS_SOURCE/challenge3/challenge3/noxus_bridge.py"
```

Os três comandos `test` devem terminar sem erro; use `echo $?` após cada um se necessário: sucesso = `0`.

Na primeira instalação, crie a cópia. **Se o destino já existir, pare e use a instalação existente; não copie por cima dela.**

```bash
mkdir -p "$HOME/noxus-lab"
test ! -e "$HOME/noxus-lab/Challenge" && \
rsync -a --exclude='.venv*' --exclude='node_modules' --exclude='.data' \
  --exclude='.noxus' --exclude='.noxus-backup' --exclude='.output' \
  --exclude='__pycache__' --exclude='.ruff_cache' --exclude='.test-results*' \
  --exclude='.env' --exclude='.env.noxus' --exclude='.env.local' \
  "$NOXUS_SOURCE/" "$HOME/noxus-lab/Challenge/"

cd "$HOME/noxus-lab/Challenge/Noxus-Aspm"
```

Essa cópia começa sem cadastros, relatórios e chaves do Windows. Não compartilhe um mesmo ambiente virtual entre os dois sistemas. As edições feitas na cópia Linux não voltam automaticamente à pasta do Windows.

### W4. Instalar o ASPM e cadastrar o desenvolvedor

**Pasta: `~/noxus-lab/Challenge/Noxus-Aspm`.**

```bash
bun run setup:local python3.12
backend/.venv-local/bin/python scripts/noxus_agent.py init
```

Responda às perguntas conforme a [tabela de cadastro](#7-cadastro-do-desenvolvedor-e-do-ativo). Para testar o Noxus como alvo, informe como pasta local o resultado de `pwd` e como URL da aplicação `http://127.0.0.1:3000`.

Sucesso: aparece `Agent conectado ao receptor http://127.0.0.1:8000/api/findings`. O servidor ainda pode estar desligado nesta etapa; o cadastro não executa scans nem testa a rede.

### W5. Instalar os quatro scanners no mesmo Ubuntu

```bash
python3.12 -m venv backend/.data/noxus-agent/scanners-venv
backend/.data/noxus-agent/scanners-venv/bin/python -m pip install \
  -e "../NOXUS-Agent-API-v2/noxus-local-v2"

backend/.data/noxus-agent/scanners-venv/bin/python -m noxus \
  --config backend/.data/noxus-agent/config.json install-tools

backend/.venv-local/bin/python scripts/noxus_agent.py doctor
```

Resultado esperado do último comando: `semgrep`, `gitleaks`, `dependency-check` e `nikto` com `true`. O instalador baixa ferramentas; exige internet e pode demorar. Se interromper, execute novamente o comando `install-tools` com o mesmo `--config`.

Não use `bun run agent:doctor` dentro do WSL: esse atalho ainda aponta para o executável Windows. Os comandos Python acima são o caminho Linux correto.

### W6. Subir o sistema e executar as primeiras análises

Abra **três terminais Ubuntu**. Em cada um, execute primeiro:

```bash
cd "$HOME/noxus-lab/Challenge/Noxus-Aspm"
```

**Terminal 1 — API, deixe aberto:**

```bash
backend/.venv-local/bin/python -m uvicorn app.main:app \
  --app-dir backend --host 127.0.0.1 --port 8000
```

**Terminal 2 — dashboard, deixe aberto:**

```bash
bun run dev --host 127.0.0.1 --strictPort
```

**Terminal 3 — conferir o receptor e executar SAST/segredos:**

```bash
curl --fail http://127.0.0.1:8000/api/health
backend/.venv-local/bin/python scripts/noxus_agent.py scan --tools semgrep gitleaks
```

Abra **http://localhost:3000** no navegador do Windows. Entre em **Vulnerabilidades** e confira **Varreduras recebidas**, mesmo se nenhum finding tiver sido encontrado.

**Terminal 3 — SCA:**

```bash
backend/.venv-local/bin/python scripts/noxus_agent.py scan --tools dependency-check
```

A primeira execução pode demorar para atualizar os dados NVD. Veja a seção 9 antes de tratar uma falha de atualização como falha do ASPM.

**Terminal 3 — DAST:** primeiro mantenha a aplicação-alvo aberta na URL cadastrada. Se estiver testando o próprio Noxus, o terminal 2 já atende a porta 3000.

```bash
backend/.venv-local/bin/python scripts/noxus_agent.py scan --tools nikto
```

**Depois que os quatro testes individuais funcionarem**, você pode executar todos de uma vez ou iniciar o monitor. Escolha um comando por vez:

```bash
backend/.venv-local/bin/python scripts/noxus_agent.py scan
```

```bash
backend/.venv-local/bin/python scripts/noxus_agent.py watch
```

`watch` permanece aberto. Ctrl+C encerra. Ele não precisa de um segundo `scan` simultâneo. Para incluir a triagem por IA, continue na seção 8.

## 5. Linux — Ubuntu 24.04

Este roteiro usa **Ubuntu 24.04 em Bash** e uma cópia completa da pasta Challenge. Em outras distribuições, os pacotes do gerenciador do sistema mudam; os comandos Python/Bun continuam os mesmos quando os pré-requisitos estiverem instalados.

### L1. Instalar as dependências do sistema

```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip \
  git curl ca-certificates unzip tar rsync nano build-essential pkg-config \
  libffi-dev libssl-dev perl libnet-ssleay-perl libio-socket-ssl-perl \
  libwww-perl openjdk-21-jdk-headless

curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.8/install.sh | bash
export NVM_DIR="$HOME/.nvm"
. "$NVM_DIR/nvm.sh"
nvm install 24
nvm alias default 24
nvm use 24

curl -fsSL https://bun.com/install | bash
export PATH="$HOME/.bun/bin:$PATH"

python3.12 --version
node --version
npm --version
bun --version
java -version
git --version
perl -v
```

### L2. Preparar a pasta do projeto

Obtenha o conjunto completo das pastas mostrado na seção 2. A instalação não clona automaticamente o código do ASPM nem o código que será analisado.

No comando abaixo, informe o **caminho absoluto da pasta Challenge recebida**, sem aspas na resposta ao prompt:

```bash
read -r -p "Caminho absoluto da pasta Challenge recebida: " NOXUS_SOURCE
test -f "$NOXUS_SOURCE/Noxus-Aspm/package.json"
test -f "$NOXUS_SOURCE/NOXUS-Agent-API-v2/noxus-local-v2/noxus/agent.py"
test -f "$NOXUS_SOURCE/challenge3/challenge3/noxus_bridge.py"
```

Se algum `test` falhar, corrija o caminho antes de continuar. Para uma instalação nova, com o destino ainda inexistente:

```bash
mkdir -p "$HOME/noxus-lab"
test ! -e "$HOME/noxus-lab/Challenge" && \
rsync -a --exclude='.venv*' --exclude='node_modules' --exclude='.data' \
  --exclude='.noxus' --exclude='.noxus-backup' --exclude='.output' \
  --exclude='__pycache__' --exclude='.ruff_cache' --exclude='.test-results*' \
  --exclude='.env' --exclude='.env.noxus' --exclude='.env.local' \
  "$NOXUS_SOURCE/" "$HOME/noxus-lab/Challenge/"

cd "$HOME/noxus-lab/Challenge/Noxus-Aspm"
```

Se a entrega já estiver em `~/noxus-lab/Challenge`, pule a cópia e use apenas o `cd`. Não reutilize ambientes virtuais copiados de outro sistema operacional.

### L3. Instalar, cadastrar e preparar scanners

```bash
bun run setup:local python3.12
backend/.venv-local/bin/python scripts/noxus_agent.py init
```

Preencha o cadastro conforme a seção 7. Em seguida:

```bash
python3.12 -m venv backend/.data/noxus-agent/scanners-venv
backend/.data/noxus-agent/scanners-venv/bin/python -m pip install \
  -e "../NOXUS-Agent-API-v2/noxus-local-v2"
backend/.data/noxus-agent/scanners-venv/bin/python -m noxus \
  --config backend/.data/noxus-agent/config.json install-tools
backend/.venv-local/bin/python scripts/noxus_agent.py doctor
```

Os quatro scanners devem aparecer com `true`. `doctor` verifica o executável inicial, não comprova que Java, rede, catálogo NVD ou um script apontado como argumento funcionem. A confirmação efetiva vem das varreduras individuais abaixo.

### L4. Iniciar API e dashboard

Abra três terminais. No início de cada um:

```bash
cd "$HOME/noxus-lab/Challenge/Noxus-Aspm"
```

**Terminal 1 — deixe aberto:**

```bash
backend/.venv-local/bin/python -m uvicorn app.main:app \
  --app-dir backend --host 127.0.0.1 --port 8000
```

**Terminal 2 — deixe aberto:**

```bash
bun run dev --host 127.0.0.1 --strictPort
```

**Terminal 3 — verificação e primeiro scan:**

```bash
curl --fail http://127.0.0.1:8000/api/health
backend/.venv-local/bin/python scripts/noxus_agent.py scan --tools semgrep gitleaks
```

Abra **http://localhost:3000**. Confira as varreduras recebidas na página **Vulnerabilidades**.

### L5. Executar SCA, DAST e monitoramento

**Terminal 3, um comando por vez:**

```bash
backend/.venv-local/bin/python scripts/noxus_agent.py scan --tools dependency-check
```

Inicie a aplicação-alvo e confirme que ela responde na URL cadastrada. Se cadastrou o próprio Noxus, use o dashboard já rodando na porta 3000.

```bash
backend/.venv-local/bin/python scripts/noxus_agent.py scan --tools nikto
```

Depois dos testes individuais, **scan completo, uma vez**:

```bash
backend/.venv-local/bin/python scripts/noxus_agent.py scan
```

Ou **monitoramento contínuo**, mantendo o terminal aberto:

```bash
backend/.venv-local/bin/python scripts/noxus_agent.py watch
```

Ctrl+C encerra. Para a IA, siga a seção 8. Não execute `bun run dev:api` ou `bun run agent:*` no Linux: esses scripts ainda usam `Scripts/python.exe`.

## 6. Windows nativo — painel, API e cadastro

Esta alternativa preserva o uso nativo do Windows. **Ela não oferece a instalação automática dos quatro scanners.** Para o caminho completo com scans deste guia, use a seção 4 e não misture os ambientes.

### N1. Instalar os pré-requisitos

**PowerShell:**

```powershell
winget install --exact --id Python.Python.3.13
winget install --exact --id Git.Git
winget install --exact --id OpenJS.NodeJS.LTS
powershell -c "irm bun.sh/install.ps1 | iex"
```

Feche e reabra o terminal. Na pasta real do projeto:

```powershell
Set-Location "C:\Users\jacki\Documents\Faculdade e tals\Challenge\Noxus-Aspm"
py -3.13 --version
node --version
npm.cmd --version
bun --version
git --version

$noxusPython = py -3.13 -c "import sys; print(sys.executable)"
bun run setup:local "$noxusPython"
bun run agent:init
```

Altere o caminho do `Set-Location` se necessário. Responda ao cadastro da seção 7. Não é preciso ativar `.venv-local` nem mudar a política de execução do PowerShell.

### N2. Executar

**Terminal 1, na raiz Noxus-Aspm:**

```powershell
bun run dev:api
```

**Terminal 2, na mesma raiz:**

```powershell
bun run dev --host 127.0.0.1 --strictPort
```

**Terminal 3:**

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
bun run agent:doctor
```

Acesse `http://localhost:3000`. Scanners ausentes aparecerão como `false`; o dashboard e a importação manual de envelopes JSON continuam disponíveis. Não execute `pip install -e .` na raiz Noxus-Aspm: o projeto Python fica em `backend`.

Se você já configurou executáveis nativos compatíveis em `commands` do cadastro, os atalhos são `bun run agent:scan --tools semgrep gitleaks`, `bun run agent:watch` e `bun run agent:flush`. **Isso não substitui a instalação nem comprova a compatibilidade nativa dos scanners.**

## 7. Cadastro do desenvolvedor e do ativo

### 7.1 Respostas solicitadas pelo init

| Pergunta | O que preencher |
|---|---|
| Pasta LOCAL do repositório | Diretório existente com o código a analisar; Linux/WSL usa caminho Linux, Windows usa caminho Windows. Enter aceita a pasta atual. |
| Nome do desenvolvedor | Seu nome; não deixe vazio. |
| Cargo | Sua função; pode ficar vazio. |
| Equipe | Seu time; pode ficar vazio. |
| URL HTTPS do repositório | Opcional: pressione Enter para usar somente a pasta local. Se informar uma URL, use HTTP(S) sem token/credenciais. Não é um comando de clone. |
| Nome do ativo | Nome reconhecível da aplicação/projeto; Enter aceita o nome da pasta. |
| URL da aplicação local | URL HTTP(S) de loopback que o Nikto deve analisar. Para testar o próprio dashboard Noxus, `http://127.0.0.1:3000`. Para outro projeto, use a porta real dele. |

O cadastro cria `backend/.data/noxus-agent/config.json`. A chave de ingestão fica também em `backend/.data/agent-connection.json` e é sincronizada pelo launcher. Não copie essas chaves para variáveis `VITE_` nem para o navegador.

O backend não recebe um ativo só porque você preencheu o `init`. O ativo aparece no inventário quando chegar seu primeiro relatório; também é possível cadastrá-lo manualmente no dashboard.

Se cadastrar manualmente **e** pelo Agent sem compartilhar o mesmo `asset.id`, serão ativos diferentes. Para um teste inicial simples, deixe o primeiro scan criar o ativo e depois confirme seu contexto no inventário.

### 7.2 O que ajustar no JSON depois do cadastro

**Linux/WSL, na raiz Noxus-Aspm:**

```bash
nano backend/.data/noxus-agent/config.json
```

**Windows nativo, na raiz Noxus-Aspm:**

```powershell
notepad backend\.data\noxus-agent\config.json
```

| Campo | Significado |
|---|---|
| `repository_path` | Pasta de código analisada. É este o nome real do campo, não `project_path`. |
| `asset.id` | Identidade estável usada para correlacionar os relatórios. Não troque a cada scan. |
| `asset.type` | O init usa `web-api`; revise se seu projeto tiver outro tipo. |
| `asset.application_url` | Alvo do Nikto. `null` permite cadastrar sem DAST, mas `scan` completo tentará Nikto e registrará falha. |
| `asset.consumed_apis` | Lista declarativa de APIs usadas pelo projeto; não há descoberta automática delas. |
| `commands` | Listas de argumentos dos scanners; o instalador preenche os caminhos. |
| `semgrep_config` | Inicialmente `p/default`, baixado do registro Semgrep. Pode apontar para regras locais. |
| `scan_timeout_seconds` | Tempo máximo por ferramenta; padrão 1800 segundos. |
| `debounce_seconds` | Agent em watch: padrão 3 segundos, separado dos 10 segundos da extensão. |
| `sca_interval_seconds` | Intervalo de SCA no watch; padrão 86400 segundos, além da inicialização e mudanças de dependências. |

Não altere a estrutura inteira para copiar um pequeno exemplo. Edite somente os campos necessários. Para mudar de Windows para Linux, faça novo cadastro na instalação Linux; não reutilize os caminhos Windows do JSON.

### 7.3 Refazer o cadastro para testar

Pare o Agent com Ctrl+C antes. Mover o arquivo guarda uma cópia recuperável; não limpa os relatórios do painel.

**Linux/WSL:**

```bash
mv -i backend/.data/noxus-agent/config.json \
  "backend/.data/noxus-agent/config.backup-$(date +%Y%m%d-%H%M%S).json"
backend/.venv-local/bin/python scripts/noxus_agent.py init
```

**Windows nativo:**

```powershell
$noxusBackup = "backend\.data\noxus-agent\config.backup-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".json"
Move-Item -LiteralPath "backend\.data\noxus-agent\config.json" -Destination $noxusBackup
bun run agent:init
```

O novo cadastro terá outro `asset.id` e `commands` vazio. No Linux/WSL, refaça W5/L3 para registrar os scanners no novo arquivo. Copie de volta o `asset.id` anterior somente se desejar continuar representando o mesmo ativo.

## 8. Ativar a triagem por IA

Você pode executar os scanners e visualizar relatórios sem um LLM. Para clicar em **Analisar pendentes**, escolha **uma** das opções abaixo.

Não existe processo separado de CrewAI para deixar aberto. O backend inicia a ponte automaticamente quando a análise é solicitada.

### 8.1 OpenRouter — inferência externa

Crie sua própria chave na [conta OpenRouter](https://openrouter.ai/settings/keys) e escolha um modelo disponível para ela no [catálogo](https://openrouter.ai/models). O [guia oficial](https://openrouter.ai/docs/quickstart) explica a autenticação.

Abra o arquivo abaixo, criando-o se não existir:

**Linux/WSL, na raiz Noxus-Aspm:**

```bash
nano ../challenge3/challenge3/.env.noxus
```

**Windows nativo, na mesma raiz:**

```powershell
notepad ..\challenge3\challenge3\.env.noxus
```

Conteúdo: substitua os dois valores indicados pelos dados da **sua** conta.

```dotenv
NOXUS_LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=SUBSTITUA_PELA_SUA_CHAVE
NOXUS_LLM_MODEL=SUBSTITUA_PELO_ID_DO_MODELO
```

O ID do modelo é o identificador do catálogo, no formato `provedor/modelo`, não a URL da página. Defini-lo explicitamente evita depender dos modelos antigos do YAML. A chave em `.env.noxus` também substitui uma chave antiga herdada do `.env` desse projeto.

Nesse modo, os achados selecionados são enviados ao OpenRouter. Custos, limites e disponibilidade dependem da conta/modelo.

### 8.2 Ollama — inferência também no computador

**Linux ou Ubuntu/WSL:**

```bash
curl -fsSL https://ollama.com/install.sh | sh
curl --fail http://127.0.0.1:11434/api/tags
```

Se a consulta falhar porque o servidor não iniciou, abra outro terminal e deixe `ollama serve` rodando. Depois, no terminal de configuração:

```bash
ollama pull qwen3:8b
ollama list
nano ../challenge3/challenge3/.env.noxus
```

Use:

```dotenv
NOXUS_LLM_PROVIDER=ollama
NOXUS_LLM_MODEL=qwen3:8b
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

O modelo [qwen3:8b](https://ollama.com/library/qwen3:8b) é um exemplo concreto para começar, não uma garantia de qualidade ou desempenho. O download e a execução exigem espaço/memória compatíveis. Um PC lento pode ultrapassar o timeout de 120 segundos de uma chamada ou os 600 segundos da análise completa.

**Windows nativo:** instale com `winget install --exact --id Ollama.Ollama`, abra o Ollama, execute `ollama pull qwen3:8b` no PowerShell e configure o mesmo `.env.noxus`. **No roteiro WSL, instale o Ollama dentro do WSL**, para o endereço acima apontar para o mesmo ambiente da API. Instruções do fornecedor: [Linux](https://docs.ollama.com/linux).

### 8.3 Conferir a configuração e usar o painel

**Linux/WSL, na raiz Noxus-Aspm:**

```bash
backend/.venv-local/bin/python ../challenge3/challenge3/noxus_bridge.py --check
```

**Windows nativo:**

```powershell
.\backend\.venv-local\Scripts\python.exe ..\challenge3\challenge3\noxus_bridge.py --check
```

Resultado esperado: `"ready": true`. Esse comando **não chama o modelo**: não valida saldo, chave junto ao provedor ou resposta real. O painel atualiza o status periodicamente; aguarde até 15 segundos ou reinicie a API.

No dashboard:

1. Abra **Vulnerabilidades** e confirme que há achados pendentes.
2. Clique em **Analisar pendentes**. Uma rodada pega até 50 pendentes.
3. Acompanhe as etapas e o histórico em **Equipe Agêntica**.
4. Consulte classificação, justificativa e evidências no detalhe do achado.
5. Repita para os demais lotes, se necessário.

Sem findings, não há lote para analisar. Um scan vazio bem-sucedido não é erro. A classificação da IA é uma sugestão; ela não resolve nem exclui automaticamente os achados.

## 9. Scanners: requisitos e leitura dos resultados

| Ferramenta | O que faz neste Agent | Para funcionar |
|---|---|---|
| Semgrep | Analisa o código local com `p/default` | Acesso às regras na primeira utilização, ou regras locais configuradas |
| Gitleaks | Busca segredos nos arquivos atuais | Executável compatível com `gitleaks dir`; não varre todo o histórico Git neste adaptador |
| Dependency-Check | Procura vulnerabilidades em dependências | Java, catálogo atualizado e ferramentas exigidas pelo ecossistema do alvo |
| Nikto | Analisa uma aplicação HTTP(S) em execução | Perl, URL local cadastrada e servidor da aplicação aberto |

Para todos os quatro concluírem, o alvo Nikto precisa existir. `asset.application_url` vazio é permitido no cadastro, mas não permite sucesso de DAST.

### NVD e primeiro SCA

O Dependency-Check precisa baixar/atualizar dados. Sem chave NVD, a atualização pode ficar lenta ou sofrer limitação. Obtenha sua chave em [NVD](https://nvd.nist.gov/developers/request-an-api-key).

Se precisar configurá-la, abra `backend/.data/noxus-agent/config.json` e acrescente `"--nvdApiKey", "SUA_CHAVE"` **ao array já existente** de `commands["dependency-check"]`, mantendo o caminho criado pelo instalador. Exemplo de estrutura, não um arquivo completo:

```json
"dependency-check": [
  "/CAMINHO/REAL/CRIADO/PELO/INSTALADOR/dependency-check.sh",
  "--nvdApiKey",
  "SUA_CHAVE_NVD"
]
```

A chave fica no cadastro local, que não deve ser versionado; o scanner a recebe como argumento do processo. O parâmetro existe na [documentação da CLI](https://dependency-check.github.io/DependencyCheck/dependency-check-cli/arguments.html).

Se doctor mostrar true mas o scan falhar, confira os executáveis registrados em commands: semgrep --version, gitleaks version, dependency-check.sh --version e perl /caminho/nikto.pl -Version. Para investigar uma falha interna, execute a ferramenta diretamente com seus parâmetros de relatório; o Agent não exibe a saída bruta dos scanners.

Dependendo do repositório analisado, o SCA também pode exigir ferramentas adicionais:

| Ecossistema do alvo | Dependência adicional; somente quando aplicável |
|---|---|
| npm | npm, já instalado com Node |
| Yarn/pnpm | `npm install --global yarn pnpm` |
| .NET | Runtime/SDK .NET 8; Ubuntu 24.04: `sudo apt install dotnet-runtime-8.0` |
| Go | `sudo apt install golang-go` |
| Ruby | Ruby + bundler-audit: `sudo apt install ruby-full` e `gem install --user-install bundler-audit`; inclua o diretório bin de gems do usuário no PATH |
| Elixir | Elixir + mix_audit; Ubuntu: `sudo apt install elixir`, depois `mix archive.install github mirego/mix_audit` |

São condicionais, não requisitos para subir o ASPM. Confira os [requisitos de análise do Dependency-Check](https://github.com/dependency-check/DependencyCheck#requirements) para seu alvo e a versão instalada.

### Confirmar que os scans realmente rodaram

No terminal, cada ferramenta registra início, status e quantidade de findings. No dashboard, confira **Varreduras recebidas**:

- `completed`: execução concluída, inclusive quando há zero findings.
- `partial`: scanner reportou cobertura incompleta.
- `failed`: houve falha; zero findings não significa ausência de vulnerabilidades.

O processo `scan` retorna código 1 se alguma ferramenta não concluiu. Mesmo assim, o relatório de falha pode chegar ao painel. API indisponível mantém resultados em `pending`; execute `flush` após restabelecer a conexão.

O inventário marca os ativos recebidos como **Encontrado automaticamente** e **Revisão pendente**. Em **Configurar → Confirmar revisão**, informe o contexto real. A origem automática permanece. Ativos cadastrados pelo botão manual têm a origem **Adicionado manualmente**.

## 10. Rotina diária e comandos

**Linux/WSL, sempre na raiz Noxus-Aspm:**

| Ação | Comando |
|---|---|
| API, terminal 1 | `backend/.venv-local/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000` |
| Dashboard, terminal 2 | `bun run dev --host 127.0.0.1 --strictPort` |
| Cadastrar | `backend/.venv-local/bin/python scripts/noxus_agent.py init` |
| Conferir scanners | `backend/.venv-local/bin/python scripts/noxus_agent.py doctor` |
| Scan completo | `backend/.venv-local/bin/python scripts/noxus_agent.py scan` |
| Só SAST | `backend/.venv-local/bin/python scripts/noxus_agent.py scan --tools semgrep` |
| Só segredos | `backend/.venv-local/bin/python scripts/noxus_agent.py scan --tools gitleaks` |
| Só SCA | `backend/.venv-local/bin/python scripts/noxus_agent.py scan --tools dependency-check` |
| Só DAST | `backend/.venv-local/bin/python scripts/noxus_agent.py scan --tools nikto` |
| Monitorar | `backend/.venv-local/bin/python scripts/noxus_agent.py watch` |
| Reenviar fila sem novo scan | `backend/.venv-local/bin/python scripts/noxus_agent.py flush` |
| Usar outro cadastro | `backend/.venv-local/bin/python scripts/noxus_agent.py scan --config /caminho/absoluto/config.json --tools semgrep` |

**Windows nativo:** os equivalentes são `bun run dev:api`, `bun run agent:init`, `bun run agent:doctor`, `bun run agent:scan`, `bun run agent:watch` e `bun run agent:flush`. `--tools` funciona em `agent:scan`; `--config` pode ser passado pelo comando `bun run agent scan --config "C:/caminho/config.json" --tools semgrep`.

| Endereço | Finalidade |
|---|---|
| `http://localhost:3000` | Dashboard |
| `http://127.0.0.1:8000/api/health` | Saúde da API integrada |
| `http://127.0.0.1:8000/docs` | Documentação interativa da API |
| `http://127.0.0.1:8000/api/findings` | Recebimento do Agent, com X-API-Key |
| `http://127.0.0.1:11434` | Ollama, somente se escolhido |

A raiz `http://127.0.0.1:8000/` pode retornar 404; ela não serve o dashboard.

No `watch`, Semgrep/Gitleaks/SCA rodam inicialmente; mudanças são observadas por polling. SCA também responde a mudanças de manifests e ao intervalo configurado. Nikto roda quando o alvo passa de offline para online. Os scanners rodam em sequência. Pare com Ctrl+C antes de iniciar outro monitor/scan usando o mesmo cadastro.

## 11. Extensão de IDE — etapa separada

A extensão **não é necessária para o fluxo Agent → API → dashboard**. O fork já tem a espera de 10 segundos para publicar diagnósticos locais; ainda não gera/envia envelopes automaticamente ao ASPM.

Instale VS Code no Windows com `winget install --exact --id Microsoft.VisualStudioCode`. Para trabalhar no Ubuntu/WSL, instale também a extensão oficial **WSL** (`ms-vscode-remote.remote-wsl`) no VS Code do Windows e abra a pasta Linux com `code .` a partir da raiz Noxus. Em Linux nativo, use o [instalador oficial](https://code.visualstudio.com/docs/setup/linux).

Com VS Code aberto na raiz **Noxus-Aspm**, execute no terminal do mesmo ambiente:

```bash
bun run ide:setup
bun run ide:prepare
bun run ide:build
bun run ide:test
```

Os mesmos quatro comandos funcionam em PowerShell, na instalação Windows. Nesse caso, instale Java com `winget install --exact --id EclipseAdoptium.Temurin.21.JDK` e reabra o terminal.

`ide:prepare` baixa servidor de linguagem e analisadores Java. Confira `java -version`: use Java 21 ou superior. Se necessário, configure `sonarlint.ls.javaHome` no VS Code para o diretório real do JDK, sem o sufixo `bin`.

Em **Executar e Depurar**, selecione **Noxus Extension for IDE** e pressione **F5**. Isso abre outra janela de desenvolvimento da extensão. Desative a extensão Sonar oficial nessa janela, pois o fork mantém os mesmos IDs internos de comandos.

O analisador OmniSharp é condicionado a credenciais do fornecedor; o instalador o ignora quando não há credenciais. Não prometa cobertura de C# sem verificar os recursos disponíveis. Não é necessário inventar conta Sonar ou configurar SonarCloud para fazer build do fork.

Mais detalhes e ponto futuro de envio: [guia da extensão](Noxus-Aspm/extensions/noxus-ide/README_NOXUS.md).

## 12. Dados, limpeza e problemas frequentes

### Armazenamento

```text
Noxus-Aspm/backend/.data/
├── noxus.local.json                 # inventário, findings e classificação atual
├── scans/                          # relatórios recebidos
├── runs/                           # entradas/saídas da triagem
├── agent-connection.json            # chave de ingestão
└── noxus-agent/
    ├── config.json                 # cadastro
    ├── agent/pending/              # fila para envio
    ├── agent/rejected/             # rejeitados para inspeção
    ├── tools/                      # scanners baixados
    └── scanners-venv/              # ambiente Python dos scanners deste guia
```

O botão **Limpar dados** do dashboard apaga relatórios e análises, inclusive os já revisados pela IA. Exige confirmação, mantém os cadastros e não pode ser desfeito. Pare o Agent para ele não enviar novos dados durante o teste. A ação é bloqueada enquanto uma análise de IA estiver em andamento.

### Problemas frequentes

| Sintoma | Causa/ação objetiva |
|---|---|
| `cd backend` tenta entrar em `backend/backend` | Você já estava dentro de backend. Volte para a raiz Noxus-Aspm antes de usar os comandos deste guia. |
| `No module named noxus` | Para operações integradas use `scripts/noxus_agent.py`. Para `install-tools`, use o Python de `scanners-venv` após instalar o pacote do Agent nele. |
| `pip install -e .` diz que falta pyproject.toml | Pasta incorreta: a raiz Noxus-Aspm é frontend; o backend Python está em `backend`. |
| `Scripts/python.exe` não existe no Linux | Use os comandos `backend/.venv-local/bin/python` das seções W/L. |
| `uv` não encontrado | O fluxo deste README usa Bun e Python diretamente; não precisa instalar uv. |
| Conexão recusada na porta 8000 | API parou/não iniciou. Confira terminal 1 e `/api/health`. |
| API respondeu 404 em `/` | Abra `/docs` ou `/api/health`; dashboard é porta 3000. |
| Falha de lock/PermissionError ao iniciar | Verifique se outra API/Agent está usando o mesmo armazenamento. Encerre a instância duplicada com Ctrl+C; não apague locks com processos ativos. |
| Vite tenta trocar a porta | Porta 3000 ocupada. Pare a instância antiga; `--strictPort` evita mudança silenciosa e problema de CORS. |
| Agent/init não pergunta novamente | Já existe config.json. Use o procedimento recuperável da seção 7.3. |
| Semgrep/Nikto/Dependency-Check não executa | Confira `doctor`, os caminhos de `commands`, Java/Perl, internet e a instalação no mesmo sistema operacional. |
| Nikto falha | A URL deve ser localhost/loopback, estar cadastrada e responder. Inicie a aplicação-alvo; não confunda sua porta com a API receptora. |
| SCA demora/falha | Atualização NVD, rede ou analisador do ecossistema podem exigir ajustes; veja seção 9. |
| Relatórios ficaram em pending | API indisponível, chave inválida ou resposta não confirmada. Corrija a API/configuração e rode `flush`. |
| Relatórios ficaram em rejected | Resposta 409, 413 ou 422: confira UUID/conteúdo, tamanho ou contrato. `flush` não reenvia rejeitados automaticamente. |
| IA não está pronta | Configure sua própria chave/modelo ou Ollama; confira a seção 8 e `--check`. |
| IA ready, mas a análise falha | Ready só verifica configuração local. Confira disponibilidade, saldo, contexto, timeout e saída do modelo. |
| Renomeou/moveu a pasta | Reabra o VS Code no caminho atual, execute setup:local com Python correto e revise `repository_path`, `agent_state_dir` e `commands` no cadastro. |
| Git mostra a pasta antiga removida | O Git pai deste checkout guardava Noxus-Aspm360 como gitlink. Regularize o versionamento no repositório pai; isso não é um erro da API. |

## 13. Inventario completo de dependencias diretas

As tabelas abaixo foram extraídas/conferidas nos manifestos desta entrega. **Faixa declarada não é necessariamente a versão resolvida no lockfile.** Use os instaladores da seção do seu sistema.

### Python: API + CrewAI + ferramentas de desenvolvimento

Instalação realizada por `bun run setup:local python3.12` no Linux, ou pelo setup com Python 3.13 no Windows.

| Pacote | Restrição |
|---|---|
| setuptools (build) | >=75 |
| fastapi | >=0.115,<1.0 |
| pydantic-settings | >=2.7,<3.0 |
| uvicorn[standard] | >=0.34,<1.0 |
| httpx | >=0.27,<1.0 |
| crewai[litellm] | >=1.0,<2.0 |
| python-dotenv | >=1.0,<2.0 |
| PyYAML | >=6.0,<7.0 |
| httpx2 | >=2.10,<3.0 |
| pytest | >=8.3,<10.0 |
| pytest-cov | >=6.0,<8.0 |
| ruff | >=0.11,<1.0 |

O backend usa Pydantic, Starlette e outras bibliotecas trazidas transitivamente pelos pacotes acima. Não é preciso criar um ambiente separado para o Challenge3 nem instalar suas antigas cópias de .venv.

### Python: Agent/instalador e Semgrep

Instalação: `scanners-venv/bin/python -m pip install -e "../NOXUS-Agent-API-v2/noxus-local-v2"`, com o caminho completo de scanners-venv mostrado em W5/L3.

| Pacote | Restrição |
|---|---|
| setuptools (build) | >=68 |
| fastapi | >=0.115,<1 |
| uvicorn | >=0.30,<1 |
| pydantic | >=2.8,<3 |
| httpx | >=0.27,<1 |
| pytest (extra test; opcional) | >=8,<10 |
| semgrep | Instalado pelo install-tools; versão não fixada no código |

Gitleaks, Nikto e Dependency-Check são executáveis externos, não bibliotecas instaladas pelo pip. O instalador consulta releases/commit na hora e guarda metadados em `backend/.data/noxus-agent/tools/installed.json`. A lista de comandos comprova os caminhos; nem toda ferramenta terá versão preenchida nesse arquivo.

### Frontend

Instalação na raiz Noxus-Aspm: `bun install --frozen-lockfile`.

<details>
<summary>Execução — lista completa</summary>

| Pacote | Restrição |
|---|---|
| `@hookform/resolvers` | `^5.2.2` |
| `@radix-ui/react-accordion` | `^1.2.12` |
| `@radix-ui/react-alert-dialog` | `^1.1.15` |
| `@radix-ui/react-aspect-ratio` | `^1.1.8` |
| `@radix-ui/react-avatar` | `^1.1.11` |
| `@radix-ui/react-checkbox` | `^1.3.3` |
| `@radix-ui/react-collapsible` | `^1.1.12` |
| `@radix-ui/react-context-menu` | `^2.2.16` |
| `@radix-ui/react-dialog` | `^1.1.15` |
| `@radix-ui/react-dropdown-menu` | `^2.1.16` |
| `@radix-ui/react-hover-card` | `^1.1.15` |
| `@radix-ui/react-label` | `^2.1.8` |
| `@radix-ui/react-menubar` | `^1.1.16` |
| `@radix-ui/react-navigation-menu` | `^1.2.14` |
| `@radix-ui/react-popover` | `^1.1.15` |
| `@radix-ui/react-progress` | `^1.1.8` |
| `@radix-ui/react-radio-group` | `^1.3.8` |
| `@radix-ui/react-scroll-area` | `^1.2.10` |
| `@radix-ui/react-select` | `^2.2.6` |
| `@radix-ui/react-separator` | `^1.1.8` |
| `@radix-ui/react-slider` | `^1.3.6` |
| `@radix-ui/react-slot` | `^1.2.4` |
| `@radix-ui/react-switch` | `^1.2.6` |
| `@radix-ui/react-tabs` | `^1.1.13` |
| `@radix-ui/react-toggle` | `^1.1.10` |
| `@radix-ui/react-toggle-group` | `^1.1.11` |
| `@radix-ui/react-tooltip` | `^1.2.8` |
| `@tailwindcss/vite` | `^4.2.1` |
| `@tanstack/react-query` | `^5.101.1` |
| `@tanstack/react-router` | `1.170.18` |
| `@tanstack/react-start` | `1.168.32` |
| `@tanstack/router-plugin` | `1.168.23` |
| `class-variance-authority` | `^0.7.1` |
| `clsx` | `^2.1.1` |
| `cmdk` | `^1.1.1` |
| `date-fns` | `^4.1.0` |
| `embla-carousel-react` | `^8.6.0` |
| `input-otp` | `^1.4.2` |
| `lucide-react` | `^0.575.0` |
| `react` | `^19.2.0` |
| `react-day-picker` | `^9.14.0` |
| `react-dom` | `^19.2.0` |
| `react-hook-form` | `7.71.2` |
| `react-resizable-panels` | `^4.6.5` |
| `recharts` | `^2.15.4` |
| `sonner` | `^2.0.7` |
| `tailwind-merge` | `^3.5.0` |
| `tailwindcss` | `^4.2.1` |
| `tw-animate-css` | `^1.3.4` |
| `vaul` | `^1.1.2` |
| `zod` | `^3.24.2` |

</details>

<details>
<summary>Build e desenvolvimento — lista completa</summary>

| Pacote | Restrição |
|---|---|
| `@eslint/js` | `^9.32.0` |
| `@types/node` | `^22.16.5` |
| `@types/react` | `^19.2.0` |
| `@types/react-dom` | `^19.2.0` |
| `@vitejs/plugin-react` | `^5.2.0` |
| `eslint` | `^9.32.0` |
| `eslint-config-prettier` | `^10.1.1` |
| `eslint-plugin-prettier` | `^5.2.6` |
| `eslint-plugin-react-hooks` | `^5.2.0` |
| `eslint-plugin-react-refresh` | `^0.4.20` |
| `globals` | `^15.15.0` |
| `nitro` | `3.0.260603-beta` |
| `prettier` | `^3.7.3` |
| `typescript` | `^5.8.3` |
| `typescript-eslint` | `^8.56.1` |
| `vite` | `8.1.5` |

</details>

### Extensão de IDE (opcional)

Instalação na raiz Noxus-Aspm: `bun run ide:setup`.

<details>
<summary>Execução — lista completa</summary>

| Pacote | Restrição |
|---|---|
| `@openpgp/web-stream-tools` | `^0.3.0` |
| `@sentry/node` | `^11.1.0` |
| `@vscode/codicons` | `^0.0.45` |
| `@vscode/webview-ui-toolkit` | `1.0.0` |
| `@xmldom/xmldom` | `^0.9.0` |
| `adm-zip` | `^0.6.0` |
| `canvas-confetti` | `^1.9.4` |
| `compare-versions` | `^6.1.1` |
| `diff` | `^9.0.0` |
| `expand-home-dir` | `^0.0.3` |
| `find-java-home` | `^2.0.0` |
| `follow-redirects` | `^1.15.11` |
| `globby` | `^16.0.0` |
| `highlight.js` | `^11.11.1` |
| `inly` | `^5.0.1` |
| `luxon` | `^3.7.2` |
| `node-html-parser` | `^9.0.0` |
| `openpgp` | `^6.3.0` |
| `path-exists` | `^5.0.0` |
| `properties` | `^1.2.1` |
| `sinon` | `^21.0.0` |
| `tar` | `^7.5.11` |
| `underscore` | `^1.13.8` |
| `vscode-languageclient` | `^10.1.1` |
| `zlib` | `^1.0.5` |

</details>

<details>
<summary>Build e desenvolvimento — lista completa</summary>

| Pacote | Restrição |
|---|---|
| `@cyclonedx/cyclonedx-npm` | `^6.0.1` |
| `@sentry/webpack-plugin` | `^5.0.0` |
| `@sonar/scan` | `^5.0.0` |
| `@types/adm-zip` | `^0.5.0` |
| `@types/chai` | `^5.2.3` |
| `@types/follow-redirects` | `^1.14.4` |
| `@types/lodash` | `^4.17.21` |
| `@types/luxon` | `^3.7.1` |
| `@types/mocha` | `^10.0.10` |
| `@types/node` | `^20.19.43` |
| `@types/vscode` | `^1.73.1` |
| `@vscode/test-electron` | `^3.0.0` |
| `@vscode/vsce` | `^4.0.0` |
| `chai` | `^6.2.1` |
| `crypto` | `^1.0.1` |
| `dateformat` | `^5.0.3` |
| `del` | `^8.0.1` |
| `expect.js` | `^0.3.1` |
| `fancy-log` | `^2.0.0` |
| `fs-extra` | `^11.4.1` |
| `glob` | `^13.0.0` |
| `istanbul-lib-coverage` | `^3.2.2` |
| `istanbul-lib-instrument` | `^6.0.3` |
| `istanbul-lib-report` | `^3.0.1` |
| `istanbul-lib-source-maps` | `^5.0.6` |
| `istanbul-reports` | `^3.2.0` |
| `map-stream` | `^0.0.7` |
| `mocha` | `^12.0.0` |
| `mocha-multi-reporters` | `^1.5.1` |
| `prettier` | `^3.7.4` |
| `stream` | `^0.0.3` |
| `through2` | `^4.0.2` |
| `ts-loader` | `^9.5.4` |
| `typescript` | `^6.0.3` |
| `unzipper` | `^0.12.3` |
| `vinyl` | `^3.0.1` |
| `webpack` | `^5.104.1` |
| `webpack-cli` | `^7.0.0` |

</details>

### Binários Java da extensão (opcionais)

Instalação na raiz: `bun run ide:prepare`.

| Artefato | Versão declarada | Condição |
|---|---|---|
| `sonarlint-language-server` | 6.0.2.79770 | Download pelo prepare |
| `sonar-go-plugin` | 1.46.0.9107 | Download pelo prepare |
| `sonar-javascript-plugin` | 14.0.0.46108 | Download pelo prepare |
| `sonar-java-plugin` | 8.44.0.48651 | Download pelo prepare |
| `sonar-java-symbolic-execution-plugin` | 8.16.4.1912 | Download pelo prepare |
| `sonar-php-plugin` | 4.1.0.16998 | Download pelo prepare |
| `sonar-python-plugin` | 5.32.0.37250 | Download pelo prepare |
| `sonar-html-plugin` | 3.28.0.8018 | Download pelo prepare |
| `sonar-xml-plugin` | 2.19.0.8138 | Download pelo prepare |
| `sonar-text-plugin` | 2.51.0.13430 | Download pelo prepare |
| `sonar-iac-plugin` | 2.20.0.24052 | Download pelo prepare |
| `sonarlint-omnisharp-plugin` | 1.47.0.102096 | Exige credenciais do fornecedor |


O prepare também extrai o bridge JavaScript do analisador correspondente. Preserve LICENSE.txt e NOTICE.txt do fork.

### Dependências transitivas e versões efetivamente instaladas

As árvores completas são mantidas em `Noxus-Aspm/bun.lock`, `Noxus-Aspm/package-lock.json`, `Noxus-Aspm/extensions/noxus-ide/package-lock.json` e `Noxus-Aspm/backend/uv.lock`. O setup Python deste guia usa pip com as faixas do pyproject; **não aplica uv.lock automaticamente**. Scanners também usam versões resolvidas no momento da instalação.

Para listar todas as bibliotecas realmente instaladas, inclusive transitivas:

**Linux/WSL, raiz Noxus-Aspm:**

```bash
backend/.venv-local/bin/python -m pip freeze
backend/.data/noxus-agent/scanners-venv/bin/python -m pip freeze
npm ls --all
npm --prefix extensions/noxus-ide ls --all
```

**Windows nativo, raiz Noxus-Aspm:**

```powershell
.\backend\.venv-local\Scripts\python.exe -m pip freeze
npm.cmd ls --all
npm.cmd --prefix extensions/noxus-ide ls --all
```

Não copie uma lista transitiva de outro PC como se fosse requisito idêntico em todos os sistemas: wheels, dependências opcionais e plataformas podem variar.

## 14. Verificação de desenvolvimento e critério de sucesso

**Linux/WSL, raiz Noxus-Aspm:**

```bash
bun run typecheck
bun run lint
bun run build
bun run ide:test
backend/.venv-local/bin/python -m pytest backend/tests/test_clear_reports.py -p no:cacheprovider
```

**Windows nativo, raiz Noxus-Aspm:**

```powershell
bun run typecheck
bun run lint
bun run build
bun run ide:test
.\backend\.venv-local\Scripts\python.exe -m pytest backend/tests/test_clear_reports.py -p no:cacheprovider
```

Esses comandos verificam código; não substituem scans reais. Considere o fluxo operacional quando:

1. `/api/health` responde e o dashboard abre na porta 3000.
2. Seu cadastro contém o projeto e desenvolvedor corretos.
3. Cada scanner aparece disponível e conclui seu scan individual.
4. Os relatórios chegam a **Varreduras recebidas**, com a origem/ferramenta corretas.
5. Os ativos aparecem no inventário e seu contexto pode ser revisado.
6. Se habilitou IA, uma análise real chega ao estado concluído e mostra justificativas.

O código foi consultado para escrever este guia; o roteiro não representa uma instalação Linux/WSL limpa executada e validada nesta sessão. O build do dashboard/fork e testes isolados já foram verificados no desenvolvimento; disponibilidade dos downloads, scanners e modelos precisa ser confirmada no ambiente de uso.

## 15. Referências do projeto

- [README do ASPM](Noxus-Aspm/README.md)
- [API e endpoints](Noxus-Aspm/backend/README.md)
- [Contrato JSON dos relatórios](Noxus-Aspm/backend/docs/CONTRATO_IMPORTACAO.md)
- [CrewAI e chatbot](Noxus-Aspm/backend/docs/INTEGRACAO_CREWAI_CHATBOT.md)
- [Guia da extensão](Noxus-Aspm/extensions/noxus-ide/README_NOXUS.md)
- [Contexto original](Noxus-Aspm/contexto/CONTEXT.md)

A documentação do produto descreve também planos futuros. Para saber o que está pronto, use a tabela da seção 1 e o código desta entrega.
