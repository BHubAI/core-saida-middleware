class CoreSaidaOrchestratorException(Exception):
    pass


class RPAException(CoreSaidaOrchestratorException):
    pass


class ObjectNotFound(CoreSaidaOrchestratorException):
    pass
