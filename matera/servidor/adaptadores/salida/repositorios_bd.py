import secrets
import sqlite3
from datetime import datetime
from typing import Optional

from dominio.errores import CorreoYaRegistrado
from dominio.modelos import (
    Dispositivo, Estado, EstadoDispositivo, LecturaGuardada, Medicion, Planta, Puntaje, Usuario,
)


def _fecha(texto: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(texto) if texto else None


def _texto(fecha: Optional[datetime]) -> Optional[str]:
    return fecha.isoformat() if fecha else None


class UsuariosBd:
    def __init__(self, bd):
        self._bd = bd

    def crear(self, correo, clave_hash):
        try:
            id_ = self._bd.escribir("INSERT INTO usuarios (correo, clave_hash) VALUES (?, ?)", correo, clave_hash)
        except sqlite3.IntegrityError:
            raise CorreoYaRegistrado("Ese correo ya está registrado")
        return Usuario(id_, correo, clave_hash)

    def por_correo(self, correo):
        filas = self._bd.consultar("SELECT * FROM usuarios WHERE correo = ?", correo)
        return Usuario(filas[0]["id"], filas[0]["correo"], filas[0]["clave_hash"]) if filas else None


class PlantasBd:
    def __init__(self, bd):
        self._bd = bd

    def crear(self, usuario_id, nombre, especie):
        id_ = "MAT-" + secrets.token_hex(3).upper()
        self._bd.escribir(
            "INSERT INTO plantas (id, nombre, especie, usuario_id) VALUES (?, ?, ?, ?)",
            id_, nombre, especie, usuario_id)
        return Planta(id_, nombre, especie, usuario_id)

    def obtener(self, planta_id):
        filas = self._bd.consultar("SELECT * FROM plantas WHERE id = ?", planta_id)
        return self._planta(filas[0]) if filas else None

    def de_usuario(self, usuario_id):
        filas = self._bd.consultar("SELECT * FROM plantas WHERE usuario_id = ? ORDER BY rowid", usuario_id)
        return [self._planta(f) for f in filas]

    @staticmethod
    def _planta(f):
        return Planta(f["id"], f["nombre"], f["especie"], f["usuario_id"])


class DispositivosBd:
    def __init__(self, bd):
        self._bd = bd

    def guardar(self, d):
        self._bd.escribir(
            "INSERT INTO dispositivos (id, planta_id, estado, ventana_hasta, generacion) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET estado = excluded.estado, "
            "ventana_hasta = excluded.ventana_hasta, generacion = excluded.generacion",
            d.id, d.planta_id, d.estado.value, _texto(d.ventana_hasta), d.generacion)

    def obtener(self, dispositivo_id):
        return self._una("SELECT * FROM dispositivos WHERE id = ?", dispositivo_id)

    def de_planta(self, planta_id):
        return self._una("SELECT * FROM dispositivos WHERE planta_id = ?", planta_id)

    def _una(self, sql, valor):
        filas = self._bd.consultar(sql, valor)
        if not filas:
            return None
        f = filas[0]
        return Dispositivo(f["id"], f["planta_id"], EstadoDispositivo(f["estado"]),
                           _fecha(f["ventana_hasta"]), f["generacion"])


class HistorialBd:
    def __init__(self, bd):
        self._bd = bd

    def agregar(self, planta_id, lectura):
        m = lectura.medicion
        self._bd.escribir(
            "INSERT INTO lecturas (planta_id, momento, humedad, luz, temperatura, estado) VALUES (?, ?, ?, ?, ?, ?)",
            planta_id, lectura.momento.isoformat(), m.humedad, m.luz, m.temperatura, lectura.estado.value)

    def recientes(self, planta_id, limite):
        filas = self._bd.consultar(
            "SELECT * FROM lecturas WHERE planta_id = ? ORDER BY momento DESC, id DESC LIMIT ?",
            planta_id, limite)
        return [
            LecturaGuardada(_fecha(f["momento"]), Medicion(f["humedad"], f["luz"], f["temperatura"]),
                            Estado(f["estado"]))
            for f in filas
        ]


class PuntajesBd:
    def __init__(self, bd):
        self._bd = bd

    def obtener(self, planta_id):
        filas = self._bd.consultar("SELECT * FROM puntajes WHERE planta_id = ?", planta_id)
        if not filas:
            return Puntaje(planta_id)
        f = filas[0]
        return Puntaje(planta_id, f["puntos"], Estado(f["estado"]) if f["estado"] else None,
                       _fecha(f["cobrado_hasta"]), _fecha(f["ultima"]))

    def guardar(self, p):
        self._bd.escribir(
            "INSERT INTO puntajes (planta_id, puntos, estado, cobrado_hasta, ultima) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(planta_id) DO UPDATE SET puntos = excluded.puntos, estado = excluded.estado, "
            "cobrado_hasta = excluded.cobrado_hasta, ultima = excluded.ultima",
            p.planta_id, p.puntos, p.estado.value if p.estado else None,
            _texto(p.cobrado_hasta), _texto(p.ultima))
