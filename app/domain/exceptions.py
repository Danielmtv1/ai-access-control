class DomainError(Exception):
    """Excepción base para errores del dominio"""
    pass

class RepositoryError(DomainError):
    """Excepción para errores del repositorio"""
    pass

class MqttMessageProcessingError(DomainError):
    """Excepción para errores en el procesamiento de mensajes MQTT"""
    pass 