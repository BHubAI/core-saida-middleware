class CoreSaidaMiddlewareException(Exception):
    pass


class RPAException(CoreSaidaMiddlewareException):
    pass


class ObjectNotFound(CoreSaidaMiddlewareException):
    pass
