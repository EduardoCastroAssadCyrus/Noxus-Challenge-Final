class IntegrationNotConfiguredError(RuntimeError):
    """Indica que uma porta futura existe, mas nenhum provedor real foi configurado."""

    def __init__(self, integration: str) -> None:
        self.integration = integration
        super().__init__(f"A integração {integration} ainda não foi configurada.")


class DuplicateAssetIdentifierError(ValueError):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"Já existe um ativo com o identificador {identifier}.")
