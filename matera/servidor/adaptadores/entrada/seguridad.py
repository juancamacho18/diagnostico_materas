from typing import Callable, Optional

from adaptadores.entrada.errores import ErrorDeEntrada


class Seguridad:
    """Único lugar donde se leen y verifican los JWT."""

    def __init__(self, verificar_token: Callable[[str], Optional[dict]],
                 dispositivo_vigente: Callable[[str, int], bool]):
        self._verificar = verificar_token
        self._vigente = dispositivo_vigente

    def identidad_de_token(self, token: str, tipo: str):
        datos = self._verificar(token)
        if datos is None or datos.get("tipo") != tipo:
            return None
        if tipo == "usuario":
            return int(datos["sub"]) if str(datos["sub"]).isdigit() else None
        return datos["sub"] if self._vigente(datos["sub"], datos["gen"]) else None

    def desde_cabecera(self, cabecera: str | None, tipo: str):
        if not cabecera or not cabecera.startswith("Bearer "):
            raise ErrorDeEntrada(401, "NO_AUTENTICADO", "Falta el token")
        identidad = self.identidad_de_token(cabecera[7:], tipo)
        if identidad is None:
            raise ErrorDeEntrada(401, "TOKEN_INVALIDO", "Token inválido o vencido")
        return identidad
