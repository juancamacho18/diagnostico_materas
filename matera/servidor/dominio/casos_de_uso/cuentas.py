from datetime import timedelta

from dominio.errores import (
    CorreoYaRegistrado, CredencialesInvalidas, DatoInvalido, DispositivoYaRegistrado,
    EspecieDesconocida,
)
from dominio.modelos import Dispositivo, EstadoDispositivo, Planta
from dominio.puertos.salida import (
    DispositivoRepositorioPuerto, EmisorTokenPuerto, EspecieRepositorioPuerto,
    HasheadorPuerto, PlantaRepositorioPuerto, RelojPuerto, UsuarioRepositorioPuerto,
)

VENTANA_EMPAREJAMIENTO = timedelta(minutes=10)
CLAVE_MINIMA = 6


class RegistrarUsuario:
    def __init__(self, usuarios: UsuarioRepositorioPuerto, hasheador: HasheadorPuerto):
        self._usuarios = usuarios
        self._hasheador = hasheador

    def ejecutar(self, correo: str, clave: str) -> int:
        correo = correo.strip().lower()
        if "@" not in correo:
            raise DatoInvalido("Correo inválido", {"campo": "correo"})
        if len(clave) < CLAVE_MINIMA:
            raise DatoInvalido(f"La clave necesita al menos {CLAVE_MINIMA} caracteres", {"campo": "clave"})
        if self._usuarios.por_correo(correo):
            raise CorreoYaRegistrado("Ese correo ya está registrado")
        return self._usuarios.crear(correo, self._hasheador.hashear(clave)).id


class IniciarSesion:
    def __init__(self, usuarios: UsuarioRepositorioPuerto, hasheador: HasheadorPuerto, emisor: EmisorTokenPuerto):
        self._usuarios = usuarios
        self._hasheador = hasheador
        self._emisor = emisor

    def ejecutar(self, correo: str, clave: str) -> str:
        usuario = self._usuarios.por_correo(correo.strip().lower())
        if usuario is None or not self._hasheador.coincide(clave, usuario.clave_hash):
            raise CredencialesInvalidas("Correo o clave incorrectos")
        return self._emisor.para_usuario(usuario.id)


class RegistrarPlanta:
    def __init__(
        self, plantas: PlantaRepositorioPuerto, dispositivos: DispositivoRepositorioPuerto,
        especies: EspecieRepositorioPuerto, reloj: RelojPuerto,
    ):
        self._plantas = plantas
        self._dispositivos = dispositivos
        self._especies = especies
        self._reloj = reloj

    def ejecutar(self, usuario_id: int, nombre: str, especie: str, dispositivo_id: str) -> Planta:
        nombre = nombre.strip()
        if not nombre:
            raise DatoInvalido("El nombre no puede estar vacío", {"campo": "nombre"})
        if self._especies.obtener(especie) is None:
            raise EspecieDesconocida(f"Especie desconocida: {especie}", {"especie": especie})
        if self._dispositivos.obtener(dispositivo_id) is not None:
            raise DispositivoYaRegistrado("Ese dispositivo ya pertenece a una planta")
        planta = self._plantas.crear(usuario_id, nombre, especie)
        self._dispositivos.guardar(Dispositivo(
            dispositivo_id, planta.id, EstadoDispositivo.PENDIENTE,
            self._reloj.ahora() + VENTANA_EMPAREJAMIENTO, 1,
        ))
        return Planta(planta.id, planta.nombre, planta.especie, planta.usuario_id, dispositivo_id)


class ListarPlantas:
    def __init__(self, plantas: PlantaRepositorioPuerto, dispositivos: DispositivoRepositorioPuerto):
        self._plantas = plantas
        self._dispositivos = dispositivos

    def ejecutar(self, usuario_id: int) -> list[Planta]:
        resultado = []
        for p in self._plantas.de_usuario(usuario_id):
            d = self._dispositivos.de_planta(p.id)
            resultado.append(Planta(p.id, p.nombre, p.especie, p.usuario_id, d.id if d else None))
        return resultado
