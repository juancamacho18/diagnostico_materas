import os
import tempfile

from app import crear_app
from pruebas.dobles import RelojFalso

SECRETO = "secreto-de-prueba-con-longitud-suficiente"
DISPOSITIVO = "ESP32-AAAA00000001"
BUENA = {"humedad": 60, "luz": 3000, "temperatura": 22}
MALA = {"humedad": 10, "luz": 3000, "temperatura": 22}


class Entorno:
    def __init__(self, tipo_tabla="csv", mqtt=None):
        self.carpeta = tempfile.TemporaryDirectory()
        self.reloj = RelojFalso()
        self.app = crear_app(tipo_tabla, os.path.join(self.carpeta.name, "t.db"), SECRETO, self.reloj, mqtt)
        self.http = self.app.test_client()

    def cerrar(self):
        if "mqtt" in self.app.extensions:
            self.app.extensions["mqtt"].detener()
        self.carpeta.cleanup()

    def usuario(self, correo="ana@correo.com", clave="clave123") -> dict:
        self.http.post("/api/usuarios", json={"correo": correo, "clave": clave})
        token = self.http.post("/api/sesion", json={"correo": correo, "clave": clave}).get_json()["token"]
        return {"Authorization": f"Bearer {token}"}

    def matera(self, cabecera=None, dispositivo=DISPOSITIVO, especie="monstera deliciosa") -> tuple:
        cabecera = cabecera or self.usuario()
        r = self.http.post("/api/plantas", headers=cabecera,
                           json={"nombre": "Mi mata", "especie": especie, "dispositivo": dispositivo})
        return cabecera, r.get_json()["id"]

    def token_dispositivo(self, dispositivo=DISPOSITIVO) -> str:
        return self.http.post(f"/api/dispositivos/{dispositivo}/emparejar").get_json()["token"]
