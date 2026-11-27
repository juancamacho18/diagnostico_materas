class ErrorDeDominio(Exception):
    codigo = "ERROR"

    def __init__(self, mensaje: str, detalle: dict | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.detalle = detalle or {}


class EspecieDesconocida(ErrorDeDominio):
    codigo = "ESPECIE_DESCONOCIDA"


class ParametroAusente(ErrorDeDominio):
    codigo = "PARAMETRO_AUSENTE"


class ValorNoNumerico(ErrorDeDominio):
    codigo = "VALOR_NO_NUMERICO"


class ValorFueraDeRangoFisico(ErrorDeDominio):
    codigo = "VALOR_FUERA_DE_RANGO_FISICO"


class CredencialesInvalidas(ErrorDeDominio):
    codigo = "CREDENCIALES_INVALIDAS"


class CorreoYaRegistrado(ErrorDeDominio):
    codigo = "CORREO_YA_REGISTRADO"


class DatoInvalido(ErrorDeDominio):
    codigo = "DATO_INVALIDO"


class PlantaNoEncontrada(ErrorDeDominio):
    codigo = "PLANTA_NO_ENCONTRADA"


class DispositivoYaRegistrado(ErrorDeDominio):
    codigo = "DISPOSITIVO_YA_REGISTRADO"


class DispositivoNoRegistrado(ErrorDeDominio):
    codigo = "DISPOSITIVO_NO_REGISTRADO"


class DispositivoAjeno(ErrorDeDominio):
    codigo = "DISPOSITIVO_AJENO"


class EmparejamientoNoDisponible(ErrorDeDominio):
    codigo = "EMPAREJAMIENTO_NO_DISPONIBLE"
