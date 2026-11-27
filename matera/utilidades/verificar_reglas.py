"""Comprueba las reglas no negociables. Correr desde la raíz: python utilidades/verificar_reglas.py"""

import ast
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVIDOR = os.path.join(RAIZ, "servidor")
DOMINIO = os.path.join(SERVIDOR, "dominio")
PROHIBIDOS = {"flask", "flask_cors", "flask_sock", "csv", "sqlite3", "json", "jwt", "werkzeug", "paho",
              "simple_websocket", "adaptadores", "app"}
ADAPTADORES = (r"\b(BaseDatos|UsuariosBd|PlantasBd|DispositivosBd|HistorialBd|PuntajesBd|EspeciesCsv|EspeciesBd|"
               r"EmisorJwt|Hasheador|RelojSistema|ClienteMqtt|CanalMqtt)\(")
CASOS_DE_USO = (r"\b(Diagnosticar|ListarEspecies|RegistrarUsuario|IniciarSesion|RegistrarPlanta|ListarPlantas|"
                r"RegistrarLectura|ConsultarEstado|ConsultarHistorial|EmparejarDispositivo|"
                r"ReemparejarDispositivo|ValidarCredencialDispositivo|AcumularPuntaje)\(")


def archivos(carpeta):
    for base, _, nombres in os.walk(carpeta):
        for nombre in nombres:
            if nombre.endswith(".py"):
                yield os.path.join(base, nombre)


def leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def rel(ruta):
    return os.path.relpath(ruta, RAIZ)


def imports_prohibidos():
    errores = []
    for ruta in archivos(DOMINIO):
        for nodo in ast.walk(ast.parse(leer(ruta))):
            modulos = [a.name for a in nodo.names] if isinstance(nodo, ast.Import) else \
                      [nodo.module or ""] if isinstance(nodo, ast.ImportFrom) else []
            errores += [f"{rel(ruta)} importa {m}" for m in modulos if m.split(".")[0] in PROHIBIDOS]
    return errores


def fuera_de_app(patron, excluir):
    errores = []
    for ruta in archivos(SERVIDOR):
        r = os.path.relpath(ruta, SERVIDOR)
        if r == "app.py" or r.startswith(excluir):
            continue
        if re.search(patron, leer(ruta)):
            errores.append(r)
    return errores


def puertos_fuera_del_dominio():
    return [rel(r) for r in archivos(os.path.join(SERVIDOR, "adaptadores"))
            if re.search(r"class \w+Puerto\b", leer(r))]


def html_en_el_backend():
    errores = [rel(os.path.join(SERVIDOR, d)) for d in ("templates", "plantillas") if os.path.isdir(os.path.join(SERVIDOR, d))]
    for ruta in archivos(SERVIDOR):
        if "pruebas" in ruta:
            continue
        if re.search(r"render_template|jinja2|<html|<!doctype", leer(ruta), re.I):
            errores.append(rel(ruta))
    return errores


def main():
    revisiones = [
        ("El dominio no importa Flask, CSV, SQL, JSON, JWT ni MQTT", imports_prohibidos()),
        ("Los adaptadores solo se instancian en app.py", fuera_de_app(ADAPTADORES, ("pruebas", "adaptadores"))),
        ("Los casos de uso solo se arman en app.py (y en pruebas)", fuera_de_app(CASOS_DE_USO, ("pruebas", "dominio"))),
        ("Los puertos se declaran en el dominio, no en los adaptadores", puertos_fuera_del_dominio()),
        ("El backend no genera HTML", html_en_el_backend()),
    ]
    fallo = False
    for titulo, problemas in revisiones:
        print(("OK    " if not problemas else "FALLA ") + titulo)
        for p in problemas:
            print("        " + p)
        fallo = fallo or bool(problemas)
    sys.exit(1 if fallo else 0)


if __name__ == "__main__":
    main()
