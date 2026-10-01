from app.ai.ports import ChatProvider
from app.ai.schemas import AuthorizedChatContext, ChatProviderResult
from app.core.errors import IntegrationNotConfiguredError


class OpenRouterChatAdapter(ChatProvider):
    """Ponto único da futura chamada HTTP para o modelo escolhido no OpenRouter."""

    async def reply(self, context: AuthorizedChatContext) -> ChatProviderResult:
        del context
        # Implementação futura:
        # 1. receber chave e modelo pela configuração do backend;
        # 2. enviar apenas o contexto já autorizado pelo ChatService;
        # 3. validar uma saída estruturada e registrar modelo/prompt/evidências;
        # 4. nunca disponibilizar shell, SQL ou scanners diretamente ao modelo.
        raise IntegrationNotConfiguredError("OpenRouter")
