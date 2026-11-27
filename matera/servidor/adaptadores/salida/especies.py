import csv

from dominio.modelos import Especie, Rango


class EspeciesCsv:
    def __init__(self, ruta: str):
        with open(ruta, newline="", encoding="utf-8") as archivo:
            self._especies = {f["especie"]: self._especie(f) for f in csv.DictReader(archivo)}

    @staticmethod
    def _especie(f) -> Especie:
        return Especie(
            f["especie"], f["nombre_comun"],
            Rango(float(f["humedad_min"]), float(f["humedad_max"])),
            Rango(float(f["luz_min"]), float(f["luz_max"])),
            Rango(float(f["temp_min"]), float(f["temp_max"])),
        )

    def obtener(self, nombre):
        return self._especies.get(nombre)

    def listar(self):
        return list(self._especies.values())


class EspeciesBd:
    def __init__(self, bd, origen: EspeciesCsv | None = None):
        self._bd = bd
        if origen is not None and not bd.consultar("SELECT 1 FROM especies LIMIT 1"):
            for e in origen.listar():
                bd.escribir(
                    "INSERT INTO especies VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    e.nombre, e.nombre_comun, e.humedad.minimo, e.humedad.maximo,
                    e.luz.minimo, e.luz.maximo, e.temperatura.minimo, e.temperatura.maximo)

    def obtener(self, nombre):
        filas = self._bd.consultar("SELECT * FROM especies WHERE nombre = ?", nombre)
        return self._especie(filas[0]) if filas else None

    def listar(self):
        return [self._especie(f) for f in self._bd.consultar("SELECT * FROM especies ORDER BY nombre")]

    @staticmethod
    def _especie(f) -> Especie:
        return Especie(
            f["nombre"], f["nombre_comun"], Rango(f["humedad_min"], f["humedad_max"]),
            Rango(f["luz_min"], f["luz_max"]), Rango(f["temp_min"], f["temp_max"]))
