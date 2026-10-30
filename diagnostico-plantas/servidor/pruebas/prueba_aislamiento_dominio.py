"""Revisa que ningun archivo de dominio/ importe tecnologia externa
(Flask, HTTP, CSV, SQL, JSON, JWT...). Si alguien lo hace, esta
prueba falla."""

import ast
import os
import unittest

_PROHIBIDOS = {
    "flask", "flask_cors", "werkzeug", "jwt", "csv", "json", "sqlite3",
    "requests", "urllib", "http", "socket", "os", "adaptadores",
}

_RAIZ_DOMINIO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dominio")


def _imports_de(ruta: str):
    with open(ruta, encoding="utf-8") as archivo:
        arbol = ast.parse(archivo.read())
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                yield alias.name.split(".")[0]
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            yield nodo.module.split(".")[0]


class PruebaAislamientoDelDominio(unittest.TestCase):
    def test_el_dominio_no_importa_tecnologia_externa(self):
        problemas = []
        for carpeta, _, archivos in os.walk(_RAIZ_DOMINIO):
            for nombre in archivos:
                if not nombre.endswith(".py"):
                    continue
                ruta = os.path.join(carpeta, nombre)
                for modulo in set(_imports_de(ruta)) & _PROHIBIDOS:
                    problemas.append(f"{os.path.relpath(ruta, _RAIZ_DOMINIO)} importa {modulo}")
        self.assertEqual(problemas, [], "El dominio importa tecnologia externa: " + "; ".join(problemas))


if __name__ == "__main__":
    unittest.main()
