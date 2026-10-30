"""
Deja listo un usuario y una matera de demostracion y muestra el token
que debe llevar el dispositivo (el ESP32 fisico o el simulador).

Con el servidor ya corriendo:
  python utilidades/preparar_demo.py --dispositivo ESP32-A3F2

El token del dispositivo solo se entrega al registrar la matera. Si
ya existia ese dispositivo, usa otro identificador o borra matera.db.
"""

import argparse
import json
import urllib.error
import urllib.request


def _llamar(url: str, cuerpo: dict, token: str = None):
    cabeceras = {"Content-Type": "application/json"}
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    peticion = urllib.request.Request(
        url, data=json.dumps(cuerpo).encode("utf-8"), headers=cabeceras, method="POST"
    )
    try:
        with urllib.request.urlopen(peticion, timeout=5) as respuesta:
            return respuesta.status, json.loads(respuesta.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read() or b"{}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:5000")
    parser.add_argument("--correo", default="demo@matera.com")
    parser.add_argument("--clave", default="demo123")
    parser.add_argument("--nombre", default="Sala, ventana")
    parser.add_argument("--especie", default="monstera deliciosa")
    parser.add_argument("--dispositivo", default="ESP32-A3F2")
    args = parser.parse_args()
    base = args.url.rstrip("/") + "/api/v1"

    codigo, _ = _llamar(f"{base}/auth/registro", {"correo": args.correo, "clave": args.clave})
    print("Usuario:", "creado" if codigo == 201 else "ya existia" if codigo == 409 else f"error {codigo}")

    codigo, datos = _llamar(f"{base}/auth/login", {"correo": args.correo, "clave": args.clave})
    if codigo != 200:
        raise SystemExit(f"No se pudo iniciar sesion: {datos}")
    token_usuario = datos["token"]

    codigo, datos = _llamar(
        f"{base}/plantas",
        {"nombre": args.nombre, "especie": args.especie, "dispositivo": args.dispositivo},
        token_usuario,
    )
    if codigo != 201:
        raise SystemExit(f"No se pudo registrar la matera: {datos}")

    print(f"Matera {datos['planta']['id']} registrada para el dispositivo {args.dispositivo}")
    print("\nToken del dispositivo (copialo en configuracion.h del firmware):\n")
    print(datos["tokenDispositivo"])
    print(
        "\nProbar con el simulador:\n"
        f"  python simulador/simulador_esp32.py --dispositivo {args.dispositivo}"
        f" --token <TOKEN> --url {args.url}"
    )


if __name__ == "__main__":
    main()
