"""Emite y verifica tokens JWT. El dominio solo conoce EmisorTokenPort;
verificar() lo usa el adaptador de entrada (seguridad.py), nunca el dominio.

Hay dos tipos de token:
  - usuario:     sirve para consultar las plantas del usuario.
  - dispositivo: solo sirve para reportar lecturas de su propio dispositivo.
"""

import time
from typing import Optional

import jwt

from dominio.puertos.salida import EmisorTokenPort

_DURACION_USUARIO = 60 * 60              # 1 hora
_DURACION_DISPOSITIVO = 60 * 60 * 24 * 90  # 90 dias: el firmware lo lleva grabado


class EmisorJWT(EmisorTokenPort):
    def __init__(self, secreto: str):
        self._secreto = secreto

    def _firmar(self, datos: dict, duracion: int) -> str:
        ahora = int(time.time())
        return jwt.encode({**datos, "iat": ahora, "exp": ahora + duracion}, self._secreto, "HS256")

    def emitir_para_usuario(self, usuario_id: str) -> str:
        return self._firmar({"tipo": "usuario", "sub": usuario_id}, _DURACION_USUARIO)

    def emitir_para_dispositivo(self, dispositivo_id: str) -> str:
        return self._firmar({"tipo": "dispositivo", "sub": dispositivo_id}, _DURACION_DISPOSITIVO)

    def verificar(self, token: str) -> Optional[dict]:
        """Devuelve {"tipo", "sub"} o None si el token no sirve."""
        try:
            datos = jwt.decode(token, self._secreto, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return None
        if datos.get("tipo") not in ("usuario", "dispositivo") or not datos.get("sub"):
            return None
        return {"tipo": datos["tipo"], "sub": datos["sub"]}
