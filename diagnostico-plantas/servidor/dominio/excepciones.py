"""Excepciones de dominio. No tienen codigo HTTP a proposito: esa
traduccion la hace el adaptador de entrada (adaptadores/entrada/errores.py)."""


class ErrorDeDominio(Exception):
    """Base comun para que los adaptadores puedan atrapar cualquiera."""


class EspecieNoSoportadaError(ErrorDeDominio):
    def __init__(self, especie: str):
        self.especie = especie
        super().__init__(f"Especie no soportada: {especie!r}")


class ParametroInvalidoError(ErrorDeDominio):
    """Un parametro esta ausente, no es numerico, o esta fuera del
    rango fisicamente posible."""

    def __init__(self, campo: str, motivo: str):
        self.campo = campo
        self.motivo = motivo
        super().__init__(f"Parametro invalido: {campo} ({motivo})")


class PlantaNoEncontradaError(ErrorDeDominio):
    def __init__(self, referencia: str):
        self.referencia = referencia
        super().__init__(f"Planta no encontrada: {referencia!r}")


class AccesoDenegadoError(ErrorDeDominio):
    """El usuario pidio una planta que no es suya."""

    def __init__(self):
        super().__init__("No tienes acceso a esta planta")


class UsuarioYaExisteError(ErrorDeDominio):
    def __init__(self, correo: str):
        self.correo = correo
        super().__init__(f"Ya existe un usuario con el correo {correo!r}")


class CredencialesInvalidasError(ErrorDeDominio):
    def __init__(self):
        super().__init__("Correo o contrasena incorrectos")


class DispositivoYaRegistradoError(ErrorDeDominio):
    def __init__(self, dispositivo_id: str):
        self.dispositivo_id = dispositivo_id
        super().__init__(f"El dispositivo {dispositivo_id!r} ya esta asociado a una planta")
