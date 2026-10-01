# NOXUS ASPM 360 - Contexto Oficial do Projeto

> Documento de contexto para desenvolvedores e agentes de IA que trabalham no repositório.
> Última atualização: 23 de agosto de 2026.

## 1. Como usar este documento

Antes de analisar, planejar ou modificar o projeto, leia este arquivo por completo.

Este documento descreve a visão de produto, as decisões arquiteturais e o escopo desejado do Noxus. Ele não comprova que cada funcionalidade já existe no código. Ao entrar no repositório:

1. inspecione o código antes de propor alterações;
2. diferencie funcionalidade implementada, parcialmente implementada e apenas planejada;
3. não substitua decisões deste documento silenciosamente;
4. quando o código divergir deste contexto, relate a divergência antes de alterá-lo;
5. nunca exponha, registre ou versione credenciais, tokens, senhas ou arquivos `.env` reais.

### Hierarquia das fontes

Em caso de dúvida, use esta ordem:

1. **Challenge Pride 2026 - Ideação:** requisitos e expectativas do desafio.
2. **NOXUS ASPM 360:** visão oficial concebida pela equipe.
3. **Este `CONTEXT.md`:** consolidação das fontes e das decisões posteriores.
4. **Código do repositório:** verdade sobre o que está implementado atualmente.

O vídeo `ASPM - Referencia.mp4` é um guia narrado do Challenge e acompanha visualmente a mesma estrutura do PDF de ideação.

---

## 2. Identidade do produto

**Nome:** Noxus ASPM 360°

**Categoria:** Application Security Posture Management (ASPM).

**Formato principal:** plataforma SaaS web, acessada pelo navegador.

**Definição consolidada:**

> O Noxus ASPM 360° é uma plataforma que centraliza findings de diferentes ferramentas de segurança, normaliza e correlaciona vulnerabilidades, acrescenta contexto técnico e de negócio, prioriza o que representa risco real e oferece orientação de remediação com apoio de agentes de IA especializados.

O Noxus **não é um scanner gigante** e não deve tentar recriar todas as ferramentas de segurança. Seu papel central é orquestrar inteligência sobre scanners existentes.

### Pergunta central do produto

> Entre todos os alertas recebidos, o que realmente representa risco crítico agora e por quê?

### Problema enfrentado

Empresas acumulam resultados de SAST, DAST, SCA, Secret Scanning e outras fontes. Isso gera:

- milhares de alertas isolados;
- vulnerabilidades duplicadas;
- pouco contexto sobre o ativo afetado;
- priorização baseada apenas na severidade técnica;
- dificuldade para saber o que corrigir primeiro;
- sobrecarga das equipes de segurança e desenvolvimento.

### Proposta de valor

O Noxus deve transformar alertas desconectados em findings contextualizados, explicáveis e acionáveis.

Fluxo conceitual:

```text
Scanners e integrações
        ↓
Ingestão de resultados
        ↓
Normalização em um modelo comum
        ↓
Correlação e deduplicação
        ↓
Contextualização pelo ativo e ambiente
        ↓
Priorização de risco
        ↓
Recomendação, dashboard, chatbot e alertas
```

---

## 3. Componentes fundamentais exigidos pelo Challenge

O Challenge apresenta cinco componentes fundamentais de um ASPM:

1. **Asset Discovery**
2. **Risk Correlation**
3. **Prioritization Engine**
4. **Remediation Guidance**
5. **Continuous Monitoring**

O MVP deve demonstrar esses cinco componentes de maneira coerente, mesmo que parte da descoberta de ativos seja declarativa em vez de uma varredura automática de toda a infraestrutura.

---

## 4. Os cinco pilares concebidos para o Noxus

### 4.1. Cérebro Central

Dashboard web centralizado acompanhado por um chatbot de segurança.

Responsabilidades planejadas:

- receber findings de todas as ferramentas integradas;
- mostrar postura de segurança consolidada;
- correlacionar e priorizar riscos;
- apresentar justificativas da prioridade;
- permitir explorar aplicações, ativos e findings;
- disponibilizar recomendações de correção;
- coletar feedback humano;
- permitir perguntas sobre alertas e modelagem de risco.

O dashboard é a superfície principal do produto. Extensão, scanners e APIs alimentam essa plataforma.

### 4.2. Guarda-Costas do Programador

Camada formada pelas quatro categorias principais de análise:

| Categoria | Ferramenta inicialmente escolhida | Função |
|---|---|---|
| SAST | Semgrep | Análise estática do código |
| DAST | Nikto | Análise da aplicação em execução |
| SCA | OWASP Dependency-Check | Dependências e vulnerabilidades conhecidas |
| Secret Scanning | Gitleaks | Segredos expostos em código e histórico |

As ferramentas encontram problemas. O Noxus recebe, organiza, correlaciona, contextualiza e prioriza seus resultados.

### 4.3. Extensão de IDE e API

A extensão aproxima o Noxus do fluxo do desenvolvedor.

Responsabilidades previstas:

- comunicar-se com a API central do Noxus;
- verificar dependências e bibliotecas;
- alertar sobre componentes vulneráveis ou potencialmente maliciosos;
- detectar segredos durante o desenvolvimento;
- enviar eventos e findings ao Cérebro Central.

A extensão deve ser um cliente do ecossistema Noxus. A lógica central de correlação e priorização não deve ficar presa à extensão.

### 4.4. Guardrails de IA

Filtro entre usuários e uma IA corporativa, guiado por riscos como prompt injection e vazamento de informações.

Esse componente é um diferencial adicional, mas não deve ofuscar o núcleo ASPM durante o MVP ou a apresentação. Primeiro o projeto precisa provar que centraliza, correlaciona, contextualiza, prioriza e orienta a remediação.

### 4.5. Equipe Agêntica

Arquitetura planejada com CrewAI e cinco agentes especializados:

1. **Agente de Feedback e Refinamento**
   - coleta e organiza feedback humano;
   - distribui aprendizados para melhorar regras, prompts e recomendações;
   - não deve alterar modelos ou regras críticas sem rastreabilidade.

2. **Chatbot de Segurança e Modelagem de Risco**
   - responde dúvidas sobre findings e correções;
   - auxilia na interpretação dos alertas;
   - apoia modelagem de risco ainda na idealização de aplicações.

3. **Agente de Correlação e Triagem**
   - correlaciona relatórios de SAST, DAST, SCA e Secret Scanning;
   - identifica possíveis duplicatas;
   - classifica possíveis falsos positivos com justificativa e confiança;
   - consolida findings relacionados.

4. **Agente de Recomendações e Resposta**
   - recebe findings já normalizados e contextualizados;
   - propõe correções e medidas de mitigação;
   - explica a recomendação com base no contexto disponível.

5. **Agente de Alertas Emergenciais**
   - trata eventos críticos em tempo hábil;
   - destaca segredos expostos, dependências maliciosas e riscos urgentes;
   - aciona os canais de alerta que estiverem implementados.

Os agentes precisam ter responsabilidades delimitadas. Evitar uma única chamada genérica ao LLM para "decidir tudo".

---

## 5. Asset Discovery viável para o MVP

### 5.1. Definições simples

**Aplicação:** um produto ou sistema de software que a empresa deseja proteger. Exemplos: loja virtual, internet banking, aplicativo mobile ou portal interno.

**Ativo:** qualquer elemento técnico pertencente a uma aplicação e relevante para sua segurança. Exemplos:

- repositório de código;
- API ou endpoint;
- hostname ou URL;
- serviço;
- banco de dados;
- container;
- pipeline CI/CD;
- componente em nuvem.

Hierarquia conceitual:

```text
Organização
└── Aplicação
    └── Ambiente
        └── Ativo
            └── Finding
```

### 5.2. Decisão para o MVP

O Noxus não precisa começar varrendo AWS, Azure, Kubernetes ou toda a rede do cliente. O MVP pode usar um **Asset Registry contextual**:

1. o usuário cadastra ou importa aplicações e ativos;
2. o usuário informa metadados de negócio e ambiente;
3. integrações enriquecem o cadastro com identificadores técnicos;
4. o Noxus relaciona cada finding ao ativo correspondente.

Campos úteis para o cadastro:

| Campo | Exemplo |
|---|---|
| Organização | Banco Noxus |
| Aplicação | Internet Banking |
| Ambiente | production, staging, test ou development |
| Tipo de ativo | repository, api, database, service ou container |
| Identificador técnico | URL, hostname, repo, branch, service name ou container ID |
| Criticidade de negócio | low, medium, high ou critical |
| Exposição à internet | true ou false |
| Dados sensíveis | true ou false |
| Dados reais | true ou false |
| Responsável | time ou pessoa responsável |

### 5.3. Como o contexto é obtido

O contexto não deve ser inventado pela IA. Ele vem de fatos verificáveis ou declarados:

- metadados cadastrados pelo cliente;
- repositório e branch informados pelo GitHub ou CI/CD;
- URL, hostname e endpoint informados pelo DAST;
- projeto, arquivo e linha informados pelo SAST;
- dependência e versão informadas pelo SCA;
- repositório, arquivo e commit informados pelo Secret Scanning.

Exemplo:

```text
Finding do scanner:
- tipo: SQL Injection
- severidade técnica: HIGH
- target: test-api.noxusbank.com/customers

Ativo cadastrado:
- hostname: test-api.noxusbank.com
- ambiente: TEST
- internet_exposed: false
- contains_real_data: false
- business_criticality: low

Conclusão do Noxus:
- severidade técnica: HIGH
- prioridade operacional: LOW ou MEDIUM, conforme a política definida
- justificativa: ambiente de testes isolado, sem dados reais e de baixa criticidade
```

A mesma vulnerabilidade em `api.noxusbank.com`, produção, exposta à internet e com dados financeiros deve receber prioridade operacional muito maior.

### 5.4. Regra de correlação

Cada integração deve preservar identificadores que permitam relacionar o finding ao ativo:

```text
finding.target/repository/service
        ↓
asset_identifier
        ↓
asset
        ↓
environment + application + business context
```

Quando não houver correspondência segura, o finding deve ficar como **não correlacionado**, com indicação para revisão. Não atribuir um ativo por adivinhação.

---

## 6. Modelo conceitual mínimo de dados

Entidades recomendadas:

### Organization

Representa a empresa cliente.

### Application

Agrupa os recursos técnicos que compõem um sistema de negócio.

Campos sugeridos: `id`, `organization_id`, `name`, `description`, `business_criticality`, `owner`.

### Environment

Representa produção, homologação, teste ou desenvolvimento.

Campos sugeridos: `id`, `application_id`, `name`, `environment_type`, `internet_exposed`, `contains_sensitive_data`, `contains_real_data`.

### Asset

Representa o elemento técnico monitorado.

Campos sugeridos: `id`, `environment_id`, `asset_type`, `name`, `identifier`, `metadata`, `active`.

### Finding

Representa um problema detectado e normalizado.

Campos sugeridos:

- `id`;
- `source_tool`;
- `source_finding_id`;
- `asset_id` opcional;
- `title` e `description`;
- `finding_type`;
- `technical_severity`;
- `cvss_score` e `cve` quando existirem;
- `repository`, `branch`, `commit`, `file`, `line`, `url`, `hostname` ou `endpoint`;
- `status`;
- `first_seen_at` e `last_seen_at`;
- `raw_payload` para auditoria;
- `correlation_group_id` opcional;
- `confidence`;
- `risk_score` e `operational_priority`;
- `priority_explanation`.

### Recommendation

Correção ou mitigação proposta para um finding.

### Feedback

Avaliação humana sobre finding, prioridade, falso positivo ou recomendação.

### AuditEvent

Registro rastreável de ingestões, correlações, decisões, alterações e ações de IA.

Esse é um modelo conceitual. Antes de criar migrations, compare-o com o schema já existente no repositório.

---

## 7. Pipeline de findings

### 7.1. Ingestão

Receber resultados por API, webhook, upload ou execução controlada de ferramentas.

### 7.2. Normalização

Converter formatos diferentes para um schema único de `Finding`, preservando o relatório bruto.

### 7.3. Correlação

Relacionar findings por identificadores e evidências como:

- aplicação e ativo;
- repositório, arquivo e linha;
- URL, host e endpoint;
- CVE, CWE e regra;
- dependência e versão;
- similaridade de título e descrição.

### 7.4. Deduplicação

Agrupar alertas equivalentes sem apagar evidências originais. Um finding consolidado deve continuar apontando para todas as fontes que contribuíram para ele.

### 7.5. Contextualização

Enriquecer o finding com ambiente, exposição, sensibilidade dos dados e criticidade do negócio.

### 7.6. Priorização

Calcular risco operacional com regras rastreáveis.

### 7.7. Explicação e remediação

Usar IA para explicar o resultado e gerar orientação contextualizada, sempre deixando claros os fatos utilizados.

---

## 8. Priorização de risco

### Princípio

Separar:

- **severidade técnica:** gravidade intrínseca relatada pelo scanner, CVSS ou regra;
- **prioridade operacional:** urgência real depois de considerar o contexto.

Uma severidade `HIGH` não deve ser silenciosamente reescrita como `LOW`. O Noxus preserva a severidade original e calcula outra dimensão: a prioridade operacional.

### Fatores previstos

- severidade técnica;
- explorabilidade e evidência de exploração;
- exposição à internet;
- ambiente;
- criticidade da aplicação ou ativo;
- presença de dados reais, pessoais, financeiros ou secretos;
- alcance do impacto;
- confiança do scanner e da correlação;
- existência de controles compensatórios;
- repetição ou confirmação por múltiplas fontes.

### Abordagem recomendada para o MVP

Usar um **Risk Engine determinístico** para calcular o score e deixar o LLM responsável por explicar o resultado e sugerir remediação.

Exemplo ilustrativo, ainda não definitivo:

```text
score_base = severidade_tecnica

produção                    aumenta o risco
exposição à internet        aumenta o risco
dados sensíveis ou reais    aumenta o risco
criticidade alta            aumenta o risco
ambiente de teste           reduz o impacto operacional
dados sintéticos            reduz o impacto operacional
isolamento de rede          reduz o impacto operacional
```

Os pesos, limites e categorias finais ainda precisam ser formalizados e testados. Evitar números arbitrários espalhados pelo frontend ou por prompts.

### Saída explicável

Uma decisão deve mostrar:

```text
Severidade técnica: HIGH
Prioridade operacional: LOW
Score: 28/100
Fatores que aumentaram o risco: SQL Injection com alta severidade
Fatores que reduziram o risco: TEST, sem internet, dados sintéticos
Confiança da correlação: HIGH
```

---

## 9. Uso seguro e responsável de IA

### A IA pode

- resumir e explicar findings;
- auxiliar na correlação quando houver evidências;
- sugerir que dois alertas são duplicados;
- classificar um alerta como possível falso positivo;
- produzir recomendações de correção;
- conversar sobre riscos e decisões;
- organizar feedback humano.

### A IA não deve

- inventar ativo, ambiente, exposição ou sensibilidade de dados;
- eliminar permanentemente findings sem rastreabilidade;
- declarar certeza quando os dados são insuficientes;
- executar correções destrutivas ou mudanças em produção sem autorização;
- sobrescrever a evidência original do scanner;
- usar segredos ou código privado fora dos limites autorizados.

### Falsos positivos

Evitar a formulação "a IA apaga falsos positivos". O comportamento seguro é:

1. marcar como possível falso positivo;
2. registrar confiança e justificativa;
3. manter a evidência original;
4. permitir confirmação ou rejeição humana;
5. registrar a decisão para auditoria e refinamento.

### Estratégia de refinamento

O documento original menciona feedback e refinamento contínuo, mas não define treinamento do modelo. Para o MVP, a estratégia mais viável é:

- prompts versionados;
- regras determinísticas versionadas;
- RAG com documentação e conhecimento autorizado;
- exemplos aprovados de decisões anteriores;
- memória estruturada de feedback;
- avaliação humana das respostas.

Fine-tuning não está confirmado como requisito. Não afirmar que o modelo é treinado internamente sem uma implementação real.

### LLM

O projeto original escolhe modelos acessados pela OpenRouter, especialmente opções gratuitas para viabilizar o protótipo. O modelo exato ainda deve ser registrado quando for escolhido, porque disponibilidade e limites podem mudar.

---

## 10. Stack originalmente proposta

| Camada | Tecnologia proposta |
|---|---|
| Linguagem principal | Python |
| API/backend | FastAPI |
| Dashboard original | Streamlit |
| Banco de dados | PostgreSQL |
| Orquestração de agentes | CrewAI |
| Provedor de modelos | OpenRouter |
| SAST | Semgrep |
| DAST | Nikto |
| SCA | OWASP Dependency-Check |
| Secret Scanning | Gitleaks |

### Atenção sobre o dashboard atual

O documento original propõe Streamlit, mas já existe um dashboard em desenvolvimento. O agente deve detectar a stack real do repositório antes de decidir qualquer migração. Se o frontend atual for React, TypeScript, Vite, Next.js ou outra tecnologia, não substituí-lo por Streamlit sem decisão explícita da equipe.

---

## 11. Escopo recomendado do MVP

O MVP deve priorizar uma história completa de ASPM, mesmo com poucas integrações:

1. cadastrar uma organização, aplicação, ambiente e ativo;
2. importar resultados reais ou controlados de scanners;
3. normalizar findings em um modelo comum;
4. correlacionar finding e ativo;
5. demonstrar deduplicação preservando as fontes;
6. calcular prioridade usando contexto;
7. mostrar a justificativa do score;
8. gerar uma recomendação de remediação;
9. permitir feedback humano;
10. apresentar tudo no dashboard.

### Demonstração ideal

Usar duas ocorrências semelhantes de SQL Injection:

- uma em ambiente de teste, isolado e com dados sintéticos;
- outra em produção, exposta à internet e com dados financeiros.

O Noxus deve preservar a alta severidade técnica de ambas, mas explicar por que a segunda possui prioridade operacional muito maior.

Essa demonstração prova, de maneira simples, Asset Registry, correlação, contexto, priorização e explicabilidade.

### Fora do núcleo imediato

Podem ser tratados como evolução futura, caso prejudiquem a entrega do fluxo principal:

- descoberta automática completa de AWS, Azure e GCP;
- inventário profundo de Kubernetes e containers;
- suporte amplo a dezenas de scanners;
- fine-tuning próprio de LLM;
- correção automática diretamente em produção;
- sistema completo de cobrança;
- automação integral de compliance;
- guardrails avançados para todos os tipos de IA.

---

## 12. Requisitos de dashboard

O dashboard deve favorecer clareza operacional. Telas ou áreas esperadas:

- visão executiva da postura de segurança;
- aplicações monitoradas;
- inventário de ativos e ambientes;
- lista de findings com filtros;
- detalhe do finding;
- severidade técnica versus prioridade operacional;
- justificativa e fatores do risco;
- evidências e ferramentas de origem;
- recomendação de correção;
- feedback e histórico de decisões;
- chatbot contextual;
- integrações e estado das análises.

Evitar dashboards puramente decorativos. Métricas devem ter fonte rastreável e, quando forem mockadas, isso precisa estar claro no código e na análise.

---

## 13. Modelo de negócio original

- SaaS com cobrança baseada na quantidade de sistemas, aplicações ou ativos monitorados;
- geração de logs e relatórios úteis para auditoria e compliance;
- posicionamento corporativo, com foco em visibilidade e redução de ruído operacional.

Afirmações de conformidade precisam ser precisas. O produto pode apoiar ISO 27001 e auditorias, mas não deve prometer certificação automática sem comprovação.

---

## 14. Diretrizes de desenvolvimento

Ao trabalhar no projeto:

- comece com análise do repositório e não com reescrita;
- preserve alterações existentes dos membros da equipe;
- proponha mudanças pequenas, verificáveis e reversíveis;
- mantenha backend, domínio e frontend separados;
- não coloque a lógica do risk score apenas no frontend;
- valide todos os dados recebidos de scanners;
- preserve `raw_payload` para auditoria, com proteção de informações sensíveis;
- implemente autorização e isolamento entre organizações;
- nunca versione `.env`, tokens, credenciais ou dados reais de clientes;
- use `.env.example` apenas com nomes e valores fictícios;
- registre decisões de IA e alterações de status;
- adicione testes para normalização, correlação e cálculo de risco;
- trate resultados de ferramentas externas como dados não confiáveis;
- evite exclusão automática de evidências.

---

## 15. Estado do projeto e questões abertas

Este documento não confirma o estado atual do código. A primeira análise do repositório deve responder:

- qual é a stack real do dashboard;
- se existe backend funcional ou somente interface;
- se há banco de dados e migrations;
- quais integrações são reais e quais são mockadas;
- como autenticação e multi-tenancy funcionam;
- quais entidades já existem;
- como o projeto é executado e testado;
- quais componentes visuais usam dados estáticos;
- quais erros de build, lint e testes existem.

Decisões de produto ainda abertas:

1. pesos e limites definitivos da matriz de risco;
2. modelo exato usado via OpenRouter;
3. estratégia definitiva de RAG, memória e feedback;
4. prioridade e profundidade dos Guardrails de IA no MVP;
5. grau de automação do Asset Discovery;
6. canais de alertas emergenciais;
7. autenticação, multi-tenancy e papéis de usuário;
8. scanners que estarão funcionais na apresentação final;
9. definição final do que será demonstrado ao vivo.

Não tomar essas decisões silenciosamente. Apresentar opções e impactos à equipe.

---

## 16. Orientação para a apresentação do Challenge

A apresentação tem aproximadamente cinco minutos e o público já atua em Cyber Security. Portanto:

- não gastar tempo excessivo definindo SAST, DAST, SCA ou ASPM;
- explicar o que será realmente desenvolvido;
- mostrar tecnologias, linguagem e ferramentas integradas;
- distinguir claramente o que já existe do que está planejado;
- explicar onde a IA é usada;
- informar o LLM escolhido;
- esclarecer como ocorrerá o refinamento ou treinamento;
- delimitar as ações de responsabilidade da IA;
- demonstrar o valor da contextualização e da priorização.

Mensagem recomendada:

> O Noxus recebe findings de múltiplos scanners, normaliza os resultados, relaciona cada finding ao ativo e ao contexto de negócio, calcula uma prioridade operacional explicável e utiliza agentes especializados para correlação, triagem, remediação, feedback e resposta a eventos críticos.

---

## 17. Critério de sucesso

O Noxus deixa de ser apenas um agregador quando consegue responder, com evidências:

1. **O que aconteceu?**
2. **Onde aconteceu?**
3. **Qual aplicação, ambiente e ativo foram afetados?**
4. **Qual é a severidade técnica?**
5. **Qual é a prioridade operacional?**
6. **Quais fatos aumentaram ou reduziram essa prioridade?**
7. **Como o problema pode ser corrigido ou mitigado?**
8. **Qual foi a participação da IA e qual foi a decisão humana?**

O fluxo central que deve orientar o produto é:

```text
Application → Environment → Asset → Finding → Context → Risk → Remediation
```

Esse é o coração do Noxus ASPM 360°.
