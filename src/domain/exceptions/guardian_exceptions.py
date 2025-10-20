"""
Excepciones relacionadas con el Guardian de seguridad.
"""


class GuardianException(Exception):
    """Excepción base para errores del Guardian."""
    pass


class MessageBlockedException(GuardianException):
    """Mensaje bloqueado por el Guardian."""
    
    def __init__(self, reason: str, threat_level: str = "unknown"):
        self.reason = reason
        self.threat_level = threat_level
        super().__init__(f"Mensaje bloqueado: {reason}")


class GuardianUnavailableException(GuardianException):
    """El servicio de Guardian no está disponible."""
    pass


class RateLimitExceededException(GuardianException):
    """Se excedió el límite de llamadas al Guardian."""
    pass
