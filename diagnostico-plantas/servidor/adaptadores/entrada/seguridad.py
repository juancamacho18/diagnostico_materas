"""Filtros que revisan el JWT antes de llegar al caso de uso. Al dominio
solo le llega el id ya verificado, nunca el token ni las cabeceras."""

from functools import wraps
from typing import Callable, Optional

from flask import g, request

from adaptadores.entrada.errores import respuesta_error


class Seguridad:
    def __init__(self, verificar_token: Callable[[str], Optional[dict]]):
        self._verificar_token = verificar_token

    def _leer_identidad(self, tipo_esperado: str):
        cabecera = request.headers.get("Authorization", "")
        if not cabecera.startswith("Bearer "):
            return None
        datos = self._verificar_token(cabecera[len("Bearer "):].strip())
        if datos is None or datos["tipo"] != tipo_esperado:
            return None
        return datos["sub"]

    def requiere_usuario(self, funcion):
        @wraps(funcion)
        def envoltura(*args, **kwargs):
            usuario_id = self._leer_identidad("usuario")
            if usuario_id is None:
                return respuesta_error("TOKEN_INVALIDO", "Falta un token de usuario valido", 401)
            g.usuario_id = usuario_id
            return funcion(*args, **kwargs)
        return envoltura

    def requiere_dispositivo(self, funcion):
        @wraps(funcion)
        def envoltura(*args, **kwargs):
            dispositivo_id = self._leer_identidad("dispositivo")
            if dispositivo_id is None:
                return respuesta_error("TOKEN_INVALIDO", "Falta un token de dispositivo valido", 401)
            g.dispositivo_id = dispositivo_id
            return funcion(*args, **kwargs)
        return envoltura
