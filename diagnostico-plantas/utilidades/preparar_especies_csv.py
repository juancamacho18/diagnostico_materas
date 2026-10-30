"""
Convierte el dataset de referencia (FloraDB Houseplants Care Sample,
Hugging Face: https://huggingface.co/datasets/Ichlibitiche/floradb-houseplants-care-sample,
licencia CC-BY-NC-4.0, nombres verificados contra GBIF) en el
especies.csv que usa el backend. No es parte del backend en si,
es un script que se corre una sola vez para generar el archivo.

El dataset trae min_lux/max_lux y min_temp_celsius/max_temp_celsius
como rangos ya definidos, asi que para luz y temperatura no hay que
inventar nada. Solo se descartan las filas con confianza "low"
(metadatos inferidos por genero, no por especie).

Para la humedad si toca decidir algo: el dataset solo trae un valor
"ideal", no un rango, asi que se arma una banda de +/-10 puntos
alrededor de ese valor. Es la unica cifra que no viene de la fuente.
"""

import csv
import os

import pandas as pd

RUTA_CSV_ENTRADA = os.path.join(
    os.path.dirname(__file__), "..", "datos_originales", "floradb_houseplants_care.csv"
)
RUTA_CSV_SALIDA = os.path.join(
    os.path.dirname(__file__), "..", "servidor", "infraestructura", "especies.csv"
)

MARGEN_HUMEDAD_PUNTOS_PORCENTUALES = 10
CONFIANZAS_ACEPTADAS = {"high", "medium"}


def preparar() -> int:
    df = pd.read_csv(RUTA_CSV_ENTRADA)

    filas_salida = []
    descartadas_por_confianza = 0

    for _, fila in df.iterrows():
        if fila["care_confidence"] not in CONFIANZAS_ACEPTADAS:
            descartadas_por_confianza += 1
            continue

        nombre = str(fila["scientific_name"]).strip().lower()
        ideal_humedad = float(fila["ideal_humidity_percent"])
        humedad_min = max(0.0, ideal_humedad - MARGEN_HUMEDAD_PUNTOS_PORCENTUALES)
        humedad_max = min(100.0, ideal_humedad + MARGEN_HUMEDAD_PUNTOS_PORCENTUALES)

        nombre_comun = fila.get("common_name")
        nombre_comun = "" if pd.isna(nombre_comun) else str(nombre_comun).strip()

        filas_salida.append(
            {
                "especie": nombre,
                "nombre_comun": nombre_comun,
                "humedad_min": round(humedad_min, 1),
                "humedad_max": round(humedad_max, 1),
                "luz_min": int(fila["min_lux"]),
                "luz_max": int(fila["max_lux"]),
                "temp_min": float(fila["min_temp_celsius"]),
                "temp_max": float(fila["max_temp_celsius"]),
            }
        )

    with open(RUTA_CSV_SALIDA, "w", newline="", encoding="utf-8") as archivo:
        columnas = [
            "especie",
            "nombre_comun",
            "humedad_min",
            "humedad_max",
            "luz_min",
            "luz_max",
            "temp_min",
            "temp_max",
        ]
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(filas_salida)

    print(f"Filas leidas del dataset: {len(df)}")
    print(f"Descartadas por confianza baja: {descartadas_por_confianza}")
    print(f"Especies escritas en {RUTA_CSV_SALIDA}: {len(filas_salida)}")
    return len(filas_salida)


if __name__ == "__main__":
    preparar()

