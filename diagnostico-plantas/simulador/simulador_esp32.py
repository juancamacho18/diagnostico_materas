"""
Simulador del ESP32: manda lecturas periodicas a la API de
dispositivos. No necesita hardware ni librerias externas.

Ademas de lecturas normales genera, de vez en cuando:
  - valores fuera de rango para la especie (la planta pasa a EN_RIESGO/CRITICO)
  - datos invalidos (texto, campos faltantes, valores imposibles, marca
    de tiempo mal escrita) para comprobar que la API los rechaza sin
    romperse.

Cada lectura lleva el dispositivo, la marca de tiempo (UTC, ISO 8601)
y los tres valores medidos.

Ejemplo:
  python simulador_esp32.py --dispositivo ESP32-A3F2 --token <TOKEN> --intervalo 3
"""

import argparse
import json
import os
import random
import time
from datetime import datetime, timezone
import urllib.error
import urllib.request

# Valores "sanos" alrededor de los cuales deriva la lectura.
_CENTRO = {"humedad": 55.0, "luz": 3000.0, "temperatura": 23.0}
_PASO = {"humedad": 3.0, "luz": 400.0, "temperatura": 0.6}
# Extremos fisicamente posibles, pero fuera de rango para casi cualquier especie.
_EXTREMOS = {
    "humedad": (3.0, 97.0),
    "luz": (20.0, 60000.0),
    "temperatura": (2.0, 42.0),
}


def _lectura_normal(estado: dict) -> dict:
    for campo in estado:
        estado[campo] += random.uniform(-_PASO[campo], _PASO[campo])
        estado[campo] += (_CENTRO[campo] - estado[campo]) * 0.1  # tiende a volver al centro
    return {
        "humedad": round(max(0.0, min(100.0, estado["humedad"])), 1),
        "luz": round(max(0.0, estado["luz"])),
        "temperatura": round(estado["temperatura"], 1),
    }


def _lectura_fuera_de_rango(estado: dict) -> dict:
    lectura = _lectura_normal(estado)
    for campo in random.sample(list(_EXTREMOS), k=random.choice([1, 2])):
        lectura[campo] = random.choice(_EXTREMOS[campo])
    return lectura


def _lectura_invalida(estado: dict) -> dict:
    lectura = _lectura_normal(estado)
    falla = random.choice(["texto", "faltante", "imposible", "nulo", "marca"])
    if falla == "texto":
        lectura["humedad"] = "abc"
    elif falla == "faltante":
        del lectura["luz"]
    elif falla == "imposible":
        lectura["temperatura"] = 999
    elif falla == "marca":
        lectura["marcaTiempo"] = "ayer por la tarde"
    else:
        lectura["humedad"] = None
    return lectura


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _enviar(url: str, token: str, lectura: dict):
    peticion = urllib.request.Request(
        url,
        data=json.dumps(lectura).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=5) as respuesta:
            return respuesta.status, respuesta.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8")
    except urllib.error.URLError as error:
        return None, str(error.reason)


def main():
    parser = argparse.ArgumentParser(description="Simulador de un ESP32 reportando lecturas")
    parser.add_argument("--url", default="http://127.0.0.1:5000", help="direccion del servidor")
    parser.add_argument("--dispositivo", required=True, help="identificador del dispositivo")
    parser.add_argument("--token", default=os.environ.get("MATERA_TOKEN"), help="token del dispositivo")
    parser.add_argument("--intervalo", type=float, default=5.0, help="segundos entre lecturas")
    parser.add_argument("--ciclos", type=int, default=0, help="cuantas lecturas enviar (0 = sin fin)")
    parser.add_argument("--fuera-de-rango", type=float, default=0.15, help="probabilidad (0 a 1)")
    parser.add_argument("--invalidas", type=float, default=0.10, help="probabilidad (0 a 1)")
    parser.add_argument("--semilla", type=int, default=None, help="para repetir la misma secuencia")
    args = parser.parse_args()

    if not args.token:
        parser.error("falta el token del dispositivo (--token o variable MATERA_TOKEN)")
    if args.semilla is not None:
        random.seed(args.semilla)

    url = f"{args.url.rstrip('/')}/api/dispositivos/{args.dispositivo}/lecturas"
    estado = dict(_CENTRO)
    enviadas = 0

    print(f"Enviando a {url} cada {args.intervalo} s (Ctrl+C para parar)")
    try:
        while args.ciclos == 0 or enviadas < args.ciclos:
            sorteo = random.random()
            if sorteo < args.invalidas:
                tipo, lectura = "INVALIDA", _lectura_invalida(estado)
            elif sorteo < args.invalidas + args.fuera_de_rango:
                tipo, lectura = "FUERA DE RANGO", _lectura_fuera_de_rango(estado)
            else:
                tipo, lectura = "normal", _lectura_normal(estado)

            lectura = {"dispositivo": args.dispositivo, "marcaTiempo": _ahora(), **lectura}
            codigo, cuerpo = _enviar(url, args.token, lectura)
            print(f"[{enviadas + 1}] {tipo:14} {json.dumps(lectura)} -> {codigo} {cuerpo.strip()}")
            enviadas += 1
            if args.ciclos == 0 or enviadas < args.ciclos:
                time.sleep(args.intervalo)
    except KeyboardInterrupt:
        print("\nSimulador detenido.")


if __name__ == "__main__":
    main()
