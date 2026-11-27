from datetime import datetime, timedelta, timezone

import jwt
from werkzeug.security import check_password_hash, generate_password_hash

DURACION_USUARIO = timedelta(hours=1)
DURACION_DISPOSITIVO = timedelta(days=90)


class EmisorJwt:
    def __init__(self, secreto: str):
        if len(secreto) < 32:
            raise ValueError("El secreto necesita al menos 32 caracteres")
        self._secreto = secreto

    def para_usuario(self, usuario_id: int) -> str:
        return self._firmar({"tipo": "usuario", "sub": str(usuario_id)}, DURACION_USUARIO)

    def para_dispositivo(self, dispositivo_id: str, generacion: int) -> str:
        return self._firmar({"tipo": "dispositivo", "sub": dispositivo_id, "gen": generacion}, DURACION_DISPOSITIVO)

    def verificar(self, token: str) -> dict | None:
        try:
            datos = jwt.decode(token, self._secreto, algorithms=["HS256"], options={"require": ["exp", "sub"]})
        except jwt.PyJWTError:
            return None
        if datos.get("tipo") == "dispositivo":
            gen = datos.get("gen")
            if isinstance(gen, bool) or not isinstance(gen, int):
                return None
        elif datos.get("tipo") != "usuario":
            return None
        return datos

    def _firmar(self, cuerpo: dict, duracion: timedelta) -> str:
        ahora = datetime.now(timezone.utc)
        return jwt.encode({**cuerpo, "iat": ahora, "exp": ahora + duracion}, self._secreto, algorithm="HS256")


class Hasheador:
    def hashear(self, clave: str) -> str:
        return generate_password_hash(clave)

    def coincide(self, clave: str, clave_hash: str) -> bool:
        return check_password_hash(clave_hash, clave)


class RelojSistema:
    def ahora(self) -> datetime:
        return datetime.now(timezone.utc)
