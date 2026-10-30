"""Hash de contrasenas con las utilidades de Werkzeug (ya viene con Flask)."""

from werkzeug.security import check_password_hash, generate_password_hash

from dominio.puertos.salida import HasheadorClavePort


class HasheadorWerkzeug(HasheadorClavePort):
    def hashear(self, clave: str) -> str:
        return generate_password_hash(clave)

    def verificar(self, clave: str, clave_hash: str) -> bool:
        return check_password_hash(clave_hash, clave)
