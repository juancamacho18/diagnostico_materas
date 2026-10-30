"""Usuarios y plantas: registro, inicio de sesion y alta de una
planta con su dispositivo."""

import uuid
from typing import Tuple

from dominio.entidades import Dispositivo, Planta, Usuario
from dominio.excepciones import (
    CredencialesInvalidasError,
    DispositivoYaRegistradoError,
    EspecieNoSoportadaError,
    ParametroInvalidoError,
    UsuarioYaExisteError,
)
from dominio.puertos.entrada import (
    IniciarSesionPort,
    RegistrarPlantaPort,
    RegistrarUsuarioPort,
)
from dominio.puertos.salida import (
    DispositivoRepositorioPort,
    EmisorTokenPort,
    HasheadorClavePort,
    HistorialLecturasPort,
    PlantaRepositorioPort,
    TablaReferenciaPort,
    UsuarioRepositorioPort,
)

_LARGO_MINIMO_CLAVE = 6


class RegistrarUsuario(RegistrarUsuarioPort):
    def __init__(self, usuarios: UsuarioRepositorioPort, hasheador: HasheadorClavePort):
        self._usuarios = usuarios
        self._hasheador = hasheador

    def ejecutar(self, correo: str, clave: str) -> str:
        correo = (correo or "").strip().lower()
        if "@" not in correo:
            raise ParametroInvalidoError("correo", "no parece un correo")
        if len(clave or "") < _LARGO_MINIMO_CLAVE:
            raise ParametroInvalidoError("clave", f"minimo {_LARGO_MINIMO_CLAVE} caracteres")
        if self._usuarios.obtener_por_correo(correo) is not None:
            raise UsuarioYaExisteError(correo)

        usuario = Usuario(uuid.uuid4().hex, correo, self._hasheador.hashear(clave))
        self._usuarios.guardar(usuario)
        return usuario.id


class IniciarSesion(IniciarSesionPort):
    def __init__(
        self,
        usuarios: UsuarioRepositorioPort,
        hasheador: HasheadorClavePort,
        emisor: EmisorTokenPort,
    ):
        self._usuarios = usuarios
        self._hasheador = hasheador
        self._emisor = emisor

    def ejecutar(self, correo: str, clave: str) -> str:
        usuario = self._usuarios.obtener_por_correo((correo or "").strip().lower())
        if usuario is None or not self._hasheador.verificar(clave or "", usuario.clave_hash):
            raise CredencialesInvalidasError()
        return self._emisor.emitir_para_usuario(usuario.id)


class RegistrarPlanta(RegistrarPlantaPort):
    def __init__(
        self,
        plantas: PlantaRepositorioPort,
        dispositivos: DispositivoRepositorioPort,
        historial: HistorialLecturasPort,
        tabla: TablaReferenciaPort,
        emisor: EmisorTokenPort,
    ):
        self._plantas = plantas
        self._dispositivos = dispositivos
        self._historial = historial
        self._tabla = tabla
        self._emisor = emisor

    def ejecutar(
        self, usuario_id: str, nombre: str, especie: str, dispositivo_id: str
    ) -> Tuple[Planta, str]:
        nombre = (nombre or "").strip()
        dispositivo_id = (dispositivo_id or "").strip()
        if not nombre:
            raise ParametroInvalidoError("nombre", "ausente")
        if not dispositivo_id:
            raise ParametroInvalidoError("dispositivo", "ausente")

        especie_encontrada = self._tabla.obtener_por_nombre(especie)
        if especie_encontrada is None:
            raise EspecieNoSoportadaError(especie)
        if self._dispositivos.obtener(dispositivo_id) is not None:
            raise DispositivoYaRegistradoError(dispositivo_id)

        planta = Planta(
            id="MAT-" + uuid.uuid4().hex[:6].upper(),
            nombre=nombre,
            especie=especie_encontrada.nombre,
            usuario_id=usuario_id,
            dispositivo_id=dispositivo_id,
        )
        self._plantas.guardar(planta)
        self._dispositivos.registrar(Dispositivo(dispositivo_id, planta.id))
        self._historial.iniciar(planta.id)
        return planta, self._emisor.emitir_para_dispositivo(dispositivo_id)
