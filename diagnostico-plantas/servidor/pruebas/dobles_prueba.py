"""Dobles de prueba: los puertos de salida en memoria, para probar el
dominio sin servidor, archivos ni base de datos."""

from typing import Dict, List, Optional

from dominio.entidades import (
    Dispositivo,
    EstadoPlanta,
    Lectura,
    Planta,
    RegistroLectura,
    Usuario,
)
from dominio.especie import Especie, RangoOptimo
from dominio.puertos.salida import (
    CatalogoEspeciesPort,
    DispositivoRepositorioPort,
    EmisorTokenPort,
    HasheadorClavePort,
    HistorialLecturasPort,
    PlantaRepositorioPort,
    TablaReferenciaPort,
    UsuarioRepositorioPort,
)


class TablaFalsa(TablaReferenciaPort, CatalogoEspeciesPort):
    def __init__(self, especies: Optional[Dict[str, Especie]] = None):
        self._especies = especies or {}

    def obtener_por_nombre(self, nombre: str) -> Optional[Especie]:
        return self._especies.get((nombre or "").strip().lower())

    def listar_todas(self) -> List[Especie]:
        return list(self._especies.values())


class HistorialFalso(HistorialLecturasPort):
    def __init__(self):
        self.registros: List[RegistroLectura] = []
        self.iniciadas: List[str] = []

    def iniciar(self, planta_id: str) -> None:
        self.iniciadas.append(planta_id)

    def guardar(self, planta_id: str, lectura: Lectura, estado: EstadoPlanta) -> None:
        self.registros.append(RegistroLectura(planta_id, lectura, estado))

    def ultima(self, planta_id: str) -> Optional[RegistroLectura]:
        propios = self.listar(planta_id, 1)
        return propios[0] if propios else None

    def listar(self, planta_id: str, limite: int) -> List[RegistroLectura]:
        propios = [r for r in self.registros if r.planta_id == planta_id]
        return list(reversed(propios))[:limite]


class PlantasFalsas(PlantaRepositorioPort):
    def __init__(self):
        self._plantas: Dict[str, Planta] = {}

    def guardar(self, planta: Planta) -> None:
        self._plantas[planta.id] = planta

    def obtener(self, planta_id: str) -> Optional[Planta]:
        return self._plantas.get(planta_id)

    def listar_por_usuario(self, usuario_id: str) -> List[Planta]:
        return [p for p in self._plantas.values() if p.usuario_id == usuario_id]


class DispositivosFalsos(DispositivoRepositorioPort):
    def __init__(self):
        self._dispositivos: Dict[str, Dispositivo] = {}

    def registrar(self, dispositivo: Dispositivo) -> None:
        self._dispositivos[dispositivo.id] = dispositivo

    def obtener(self, dispositivo_id: str) -> Optional[Dispositivo]:
        return self._dispositivos.get(dispositivo_id)


class UsuariosFalsos(UsuarioRepositorioPort):
    def __init__(self):
        self._usuarios: Dict[str, Usuario] = {}

    def guardar(self, usuario: Usuario) -> None:
        self._usuarios[usuario.correo] = usuario

    def obtener_por_correo(self, correo: str) -> Optional[Usuario]:
        return self._usuarios.get(correo)


class HasheadorFalso(HasheadorClavePort):
    def hashear(self, clave: str) -> str:
        return "hash:" + clave

    def verificar(self, clave: str, clave_hash: str) -> bool:
        return clave_hash == "hash:" + clave


class EmisorFalso(EmisorTokenPort):
    def emitir_para_usuario(self, usuario_id: str) -> str:
        return "token-usuario-" + usuario_id

    def emitir_para_dispositivo(self, dispositivo_id: str) -> str:
        return "token-dispositivo-" + dispositivo_id


def especie_de_prueba(nombre: str = "sansevieria trifasciata") -> Especie:
    return Especie(
        nombre=nombre,
        humedad=RangoOptimo(20.0, 45.0),
        luz=RangoOptimo(200.0, 1500.0),
        temperatura=RangoOptimo(15.0, 29.0),
        nombre_comun="Lengua de suegra",
    )
