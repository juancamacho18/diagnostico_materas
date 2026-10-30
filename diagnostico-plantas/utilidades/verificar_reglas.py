"""Comprueba las reglas no negociables de la arquitectura.
Correr desde la raiz del proyecto: python utilidades/verificar_reglas.py"""

import ast
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVIDOR = os.path.join(RAIZ, "servidor")
DOMINIO = os.path.join(SERVIDOR, "dominio")
PROHIBIDOS = {"flask", "csv", "sqlite3", "json", "jwt", "werkzeug", "flask_cors", "adaptadores"}
ADAPTADORES = r"\b(TablaCSV|TablaBD|HistorialBD|PlantasBD|UsuariosBD|EmisorJWT|HasheadorWerkzeug)\("


def archivos(carpeta):
    for base, _, nombres in os.walk(carpeta):
        for nombre in nombres:
            if nombre.endswith(".py"):
                yield os.path.join(base, nombre)


def imports_prohibidos():
    errores = []
    for ruta in archivos(DOMINIO):
        for nodo in ast.walk(ast.parse(open(ruta, encoding="utf-8").read())):
            if isinstance(nodo, ast.Import):
                modulos = [a.name for a in nodo.names]
            elif isinstance(nodo, ast.ImportFrom):
                modulos = [nodo.module or ""]
            else:
                continue
            for modulo in modulos:
                if modulo.split(".")[0] in PROHIBIDOS:
                    errores.append(f"{os.path.relpath(ruta, RAIZ)} importa {modulo}")
    return errores


def menciones_de_jwt():
    return [
        os.path.relpath(r, RAIZ)
        for r in archivos(DOMINIO)
        if "jwt" in open(r, encoding="utf-8").read().lower()
    ]


def adaptadores_fuera_de_app():
    errores = []
    for ruta in archivos(SERVIDOR):
        relativa = os.path.relpath(ruta, SERVIDOR)
        if relativa == "app.py" or relativa.startswith(("adaptadores", "pruebas_adaptadores")):
            continue
        if re.search(ADAPTADORES, open(ruta, encoding="utf-8").read()):
            errores.append(relativa)
    return errores


def main():
    revisiones = [
        ("El dominio no importa Flask, CSV, SQL, JSON ni JWT", imports_prohibidos()),
        ("El dominio no menciona JWT", menciones_de_jwt()),
        ("Los adaptadores solo se instancian en app.py", adaptadores_fuera_de_app()),
    ]
    fallo = False
    for titulo, problemas in revisiones:
        print(("OK    " if not problemas else "FALLA ") + titulo)
        for problema in problemas:
            print("        " + problema)
        fallo = fallo or bool(problemas)
    sys.exit(1 if fallo else 0)


if __name__ == "__main__":
    main()
