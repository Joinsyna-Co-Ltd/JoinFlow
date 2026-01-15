class JoinFlowError(Exception):
    """Base exception for all JoinFlow components."""


class ValidationError(JoinFlowError):
    pass


class ConfigurationError(JoinFlowError):
    pass


class RetrievalError(JoinFlowError):
    pass
