"""
Prueba la API con lecturas reales en vez de valores inventados a mano.

El archivo lecturas_sensor_iot_salud.csv trae 10 unidades de sensor
sin nombre de especie, asi que no sirve para armar especies.csv (ver
README). Pero tiene la forma de lo que mandaria un ESP32 real, asi
que aca se usa para eso: toma filas reales del CSV, las manda contra
una especie del catalogo, y compara la etiqueta del dataset con el
diagnostico que da la API. No tienen que coincidir necesariamente --
el dataset clasifica con su propia regla (sobre todo humedad);
nuestra API compara contra los rangos de una especie real y usa los
3 parametros.

Uso:
    python utilidades/probar_con_lecturas_sensor.py [especie] [n_filas]

Ejemplo:
    python utilidades/probar_con_lecturas_sensor.py "aloe barbadensis" 6

Requiere el servidor corriendo (python servidor/ejecutar.py).
"""

import csv
import os
import sys
import urllib.error
import urllib.request
import json

RUTA_CSV_SENSOR = os.path.join(
    os.path.dirname(__file__), "..", "datos_originales", "lecturas_sensor_iot_salud.csv"
)
API_URL = os.environ.get("API_URL", "http://127.0.0.1:5000/api/v1/diagnosticos")


def leer_muestra(n_por_estado: int):
    filas_por_estado = {"Healthy": [], "Moderate Stress": [], "High Stress": []}
    with open(RUTA_CSV_SENSOR, newline="", encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            estado = fila["Plant_Health_Status"]
            if estado in filas_por_estado and len(filas_por_estado[estado]) < n_por_estado:
                filas_por_estado[estado].append(fila)

    muestra = []
    for filas in filas_por_estado.values():
        muestra.extend(filas)
    return muestra


def diagnosticar(especie: str, humedad: float, luz: float, temperatura: float):
    payload = json.dumps(
        {"especie": especie, "humedad": humedad, "luz": luz, "temperatura": temperatura}
    ).encode("utf-8")
    peticion = urllib.request.Request(
        API_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(peticion, timeout=5) as respuesta:
            return json.loads(respuesta.read())
    except urllib.error.HTTPError as error:
        return json.loads(error.read())
    except urllib.error.URLError:
        print("No se pudo conectar con la API. ¿Esta corriendo 'python servidor/ejecutar.py'?")
        sys.exit(1)


def main():
    especie = sys.argv[1] if len(sys.argv) > 1 else "aloe barbadensis"
    n_por_estado = int(sys.argv[2]) if len(sys.argv) > 2 else 2

    print(f"Comparando contra la especie: {especie!r}\n")
    muestra = leer_muestra(n_por_estado)

    for fila in muestra:
        humedad = float(fila["Soil_Moisture"])
        luz = float(fila["Light_Intensity"])
        temperatura = float(fila["Ambient_Temperature"])
        etiqueta_original = fila["Plant_Health_Status"]

        resultado = diagnosticar(especie, humedad, luz, temperatura)

        print(f"Lectura real (Plant_ID={fila['Plant_ID']}, etiqueta dataset='{etiqueta_original}')")
        print(f"  humedad={humedad:.1f}%  luz={luz:.0f}lux  temperatura={temperatura:.1f}C")
        if "error" in resultado:
            print(f"  -> API respondio error: {resultado['error']} ({resultado.get('mensaje')})")
        else:
            print(f"  -> API respondio: {resultado['estado']}")
            for parametro in resultado["parametros"]:
                print(f"     {parametro['nombre']}: {parametro['estado']}")
        print()


if __name__ == "__main__":
    main()
