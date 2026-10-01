# Validação da entrega v2

Executada em Linux com Python 3.12, FastAPI 0.142.2 e Pydantic 2.13.5.

- **35 testes automatizados passaram.**
- API iniciada em processo Uvicorn separado, acessada por HTTP real em loopback.
- CLI `demo` enviou envelope à API e a fila foi removida após confirmação.
- Envelope da futura extensão enviado à rota dedicada por HTTP real.
- Dois JSONs persistidos e dashboard retornou dois scans/dois findings.
- Reinício da app factory preservou registros no teste de persistência.
- Reenvios simultâneos geraram um único arquivo; colisão com conteúdo diferente retornou 409.
- Triagem permaneceu após nova ocorrência, com histórico.
- Contratos inválidos, datas sem fuso e credenciais em URL foram rejeitados.
- Corpo acima de 10 MiB foi rejeitado.
- Campos Secret/Match do Gitleaks não apareceram no resultado normalizado; campos livres SECRET foram substituídos na API.
- Fila offline preservou UUID/conteúdo; rejeição permanente foi mantida em rejected.
- Monitoramento de commit, dependência e aplicação online foi validado com eventos simulados.
- Um subprocesso real simulou a interface CLI Semgrep e gerou relatório de teste.
- ZIP com tentativa de sair do diretório de extração foi rejeitado.

## Não validado neste ambiente

- Instalação online dos quatro scanners e execução real deles sobre um projeto.
- Comportamento no Windows/WSL do usuário; testes executados em Linux.
- Nikto contra aplicação real; os parsers usam fixtures sintéticas do formato suportado.
- Integração com SonarQube for IDE real: extensão ainda não existe; somente contrato, rota e helper estão entregues.
- Longa duração, cargas grandes, atualização de bases NVD e todas as versões futuras de relatórios.
- Helper TypeScript não foi compilado/executado; é referência para a futura extensão.

Houve um aviso de depreciação do TestClient Starlette em relação ao transporte httpx do ambiente; não houve falhas. Não há testes com PostgreSQL/SQLite porque não são usados nesta versão.
