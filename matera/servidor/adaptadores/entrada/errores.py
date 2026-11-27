from dominio.errores import (
    CorreoYaRegistrado, CredencialesInvalidas, DatoInvalido, DispositivoAjeno,
    DispositivoNoRegistrado, DispositivoYaRegistrado, EmparejamientoNoDisponible,
    ErrorDeDominio, EspecieDesconocida, ParametroAusente, PlantaNoEncontrada,
    ValorFueraDeRangoFisico, ValorNoNumerico,
)

ESTADO_HTTP = {
    EspecieDesconocida: 404,
    ParametroAusente: 400,
    ValorNoNumerico: 400,
    ValorFueraDeRangoFisico: 422,
    CredencialesInvalidas: 401,
    CorreoYaRegistrado: 409,
    DatoInvalido: 400,
    PlantaNoEncontrada: 404,
    DispositivoYaRegistrado: 409,
    DispositivoNoRegistrado: 404,
    DispositivoAjeno: 403,
    EmparejamientoNoDisponible: 403,
}


class ErrorDeEntrada(Exception):
    def __init__(self, estado: int, codigo: str, mensaje: str, detalle: dict | None = None):
        super().__init__(mensaje)
        self.estado, self.codigo, self.mensaje, self.detalle = estado, codigo, mensaje, detalle or {}


def cuerpo_de_error(codigo: str, mensaje: str, detalle: dict | None = None) -> dict:
    return {"error": codigo, "mensaje": mensaje, "detalle": detalle or {}}


def describir(error: Exception) -> tuple[int, dict]:
    if isinstance(error, ErrorDeEntrada):
        return error.estado, cuerpo_de_error(error.codigo, error.mensaje, error.detalle)
    if isinstance(error, ErrorDeDominio):
        return ESTADO_HTTP.get(type(error), 400), cuerpo_de_error(error.codigo, error.mensaje, error.detalle)
    return 500, cuerpo_de_error("ERROR_INTERNO", "Error interno")
