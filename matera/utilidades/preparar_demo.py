"""Crea el usuario de demostración y una matera para el dispositivo dado."""

import argparse
import json
import urllib.error
import urllib.request

CORREO, CLAVE = "demo@matera.com", "demo123"


def llamar(base, ruta, cuerpo=None, token=None, metodo="POST"):
    cabeceras = {"Content-Type": "application/json"}
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    try:
        with urllib.request.urlopen(urllib.request.Request(base + ruta, datos, cabeceras, metodo)) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dispositivo", required=True)
    p.add_argument("--servidor", default="http://127.0.0.1:5000")
    p.add_argument("--especie", default="monstera deliciosa")
    p.add_argument("--nombre", default="Mi monstera")
    a = p.parse_args()
    llamar(a.servidor, "/api/usuarios", {"correo": CORREO, "clave": CLAVE})
    _, sesion = llamar(a.servidor, "/api/sesion", {"correo": CORREO, "clave": CLAVE})
    estado, cuerpo = llamar(a.servidor, "/api/plantas", {"nombre": a.nombre, "especie": a.especie, "dispositivo": a.dispositivo}, sesion["token"])
    if estado == 201:
        print(f"Matera {cuerpo['id']} creada. Tienes 10 minutos para encender el dispositivo.")
    else:
        print(f"No se creó: {cuerpo.get('error')} - {cuerpo.get('mensaje')}")
    print(f"Usuario: {CORREO} / {CLAVE}")


if __name__ == "__main__":
    main()
