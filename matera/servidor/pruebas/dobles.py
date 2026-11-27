from datetime import datetime, timedelta, timezone

from dominio.modelos import Especie, Planta, Puntaje, Rango, Usuario

INICIO = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
MONSTERA = Especie("monstera", "Monstera", Rango(50, 70), Rango(1500, 5000), Rango(18, 30))


class RelojFalso:
    def __init__(self):
        self.t = INICIO

    def ahora(self):
        return self.t

    def avanzar(self, **kw):
        self.t += timedelta(**kw)


class EspeciesFalsas:
    def __init__(self, *especies):
        self._d = {e.nombre: e for e in (especies or (MONSTERA,))}

    def obtener(self, nombre):
        return self._d.get(nombre)

    def listar(self):
        return list(self._d.values())


class UsuariosFalsos:
    def __init__(self):
        self.d = {}

    def crear(self, correo, clave_hash):
        u = Usuario(len(self.d) + 1, correo, clave_hash)
        self.d[correo] = u
        return u

    def por_correo(self, correo):
        return self.d.get(correo)


class PlantasFalsas:
    def __init__(self):
        self.d = {}

    def crear(self, usuario_id, nombre, especie):
        p = Planta(f"MAT-{len(self.d) + 1:06X}", nombre, especie, usuario_id)
        self.d[p.id] = p
        return p

    def obtener(self, planta_id):
        return self.d.get(planta_id)

    def de_usuario(self, usuario_id):
        return [p for p in self.d.values() if p.usuario_id == usuario_id]


class DispositivosFalsos:
    def __init__(self):
        self.d = {}

    def guardar(self, dispositivo):
        self.d[dispositivo.id] = dispositivo

    def obtener(self, dispositivo_id):
        return self.d.get(dispositivo_id)

    def de_planta(self, planta_id):
        return next((x for x in self.d.values() if x.planta_id == planta_id), None)


class HistorialFalso:
    def __init__(self):
        self.d = {}

    def agregar(self, planta_id, lectura):
        self.d.setdefault(planta_id, []).insert(0, lectura)

    def recientes(self, planta_id, limite):
        return self.d.get(planta_id, [])[:limite]


class PuntajesFalsos:
    def __init__(self):
        self.d = {}

    def obtener(self, planta_id):
        return self.d.get(planta_id, Puntaje(planta_id))

    def guardar(self, puntaje):
        self.d[puntaje.planta_id] = puntaje


class HasheadorFalso:
    def hashear(self, clave):
        return "h:" + clave

    def coincide(self, clave, clave_hash):
        return clave_hash == "h:" + clave


class EmisorFalso:
    def para_usuario(self, usuario_id):
        return f"usuario-{usuario_id}"

    def para_dispositivo(self, dispositivo_id, generacion):
        return f"dispositivo-{dispositivo_id}-g{generacion}"
