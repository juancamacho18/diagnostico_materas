import ast
import pathlib
import unittest

PROHIBIDOS = {"flask", "flask_cors", "flask_sock", "jwt", "sqlite3", "csv", "json", "paho", "requests",
              "simple_websocket", "werkzeug", "pandas", "adaptadores", "app"}
DOMINIO = pathlib.Path(__file__).resolve().parent.parent / "dominio"


class PruebaAislamientoDelDominio(unittest.TestCase):
    def test_el_dominio_no_importa_infraestructura(self):
        archivos = list(DOMINIO.rglob("*.py"))
        self.assertGreater(len(archivos), 10)
        for archivo in archivos:
            for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))):
                modulos = []
                if isinstance(nodo, ast.Import):
                    modulos = [a.name for a in nodo.names]
                elif isinstance(nodo, ast.ImportFrom) and nodo.module:
                    modulos = [nodo.module]
                for m in modulos:
                    self.assertNotIn(m.split(".")[0], PROHIBIDOS, f"{archivo.name} importa {m}")


if __name__ == "__main__":
    unittest.main()
