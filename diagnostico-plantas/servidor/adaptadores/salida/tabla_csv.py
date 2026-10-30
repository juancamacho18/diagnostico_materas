"""Tabla de referencia leida de un CSV. Implementa los mismos puertos
que tabla_bd.py; cual se usa se decide en app.py."""

import csv
from typing import Dict, List, Optional

from dominio.especie import Especie, RangoOptimo
from dominio.puertos.salida import CatalogoEspeciesPort, TablaReferenciaPort


class TablaCSV(TablaReferenciaPort, CatalogoEspeciesPort):
    def __init__(self, ruta_csv: str):
        self._ruta_csv = ruta_csv
        self._cache: Optional[Dict[str, Especie]] = None

    def _cargar(self) -> Dict[str, Especie]:
        if self._cache is not None:
            return self._cache

        especies: Dict[str, Especie] = {}
        with open(self._ruta_csv, newline="", encoding="utf-8") as archivo:
            for fila in csv.DictReader(archivo):
                nombre = fila["especie"].strip().lower()
                especies[nombre] = Especie(
                    nombre=nombre,
                    humedad=RangoOptimo(float(fila["humedad_min"]), float(fila["humedad_max"])),
                    luz=RangoOptimo(float(fila["luz_min"]), float(fila["luz_max"])),
                    temperatura=RangoOptimo(float(fila["temp_min"]), float(fila["temp_max"])),
                    nombre_comun=(fila.get("nombre_comun") or "").strip(),
                )
        self._cache = especies
        return especies

    def obtener_por_nombre(self, nombre: str) -> Optional[Especie]:
        return self._cargar().get((nombre or "").strip().lower())

    def listar_todas(self) -> List[Especie]:
        return sorted(self._cargar().values(), key=lambda e: e.nombre)
