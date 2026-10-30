"""Arma los commits de la Fase 2 en el orden que pide la prueba de cambio
y comprueba que el commit del dispositivo no toca el dominio.

Se corre desde la raiz de este proyecto, apuntando a tu clon del
repositorio (el que ya tiene la Fase 1):

  python utilidades/crear_historial_git.py --repo ../diagnostico-plantas-repo

Usa tu configuracion de git (nombre y correo). No sube nada: despues
revisas con git log y haces el push tu mismo.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CAPAS_VIEJAS = [
    "servidor/aplicacion", "servidor/infraestructura", "servidor/presentacion",
    "servidor/ejecutar.py", "servidor/dominio", "servidor/pruebas",
    "interfaz", "servidor/requirements.txt", "README.md",
]

ENTRADA_DISPOSITIVOS = [
    "servidor/adaptadores/entrada/api_dispositivos.py",
    "servidor/app.py",
    "simulador",
]

COMMITS = [
    ("Mover la logica a un dominio con puertos de entrada y de salida", [
        "servidor/__init__.py", "servidor/dominio", "servidor/pruebas",
    ]),
    ("Agregar adaptadores de salida: tabla CSV, tabla en BD, historial, usuarios y dispositivos", [
        "servidor/adaptadores/__init__.py", "servidor/adaptadores/salida",
        "servidor/pruebas_adaptadores/__init__.py",
        "servidor/pruebas_adaptadores/prueba_adaptadores_salida.py",
        "servidor/requirements.txt",
    ]),
    ("Agregar API del front, seguridad con JWT y punto de composicion", [
        "servidor/adaptadores/entrada/__init__.py",
        "servidor/adaptadores/entrada/api_front.py",
        "servidor/adaptadores/entrada/dtos.py",
        "servidor/adaptadores/entrada/errores.py",
        "servidor/adaptadores/entrada/seguridad.py",
        "servidor/app.py",
    ]),
    ("Agregar adaptador de dispositivos y simulador del ESP32", ENTRADA_DISPOSITIVOS),
    ("Agregar front que se actualiza solo", ["interfaz"]),
    ("Agregar firmware del ESP32 con potenciometros", ["firmware_esp32"]),
    ("Agregar pruebas de la API y verificacion de las reglas", [
        "servidor/pruebas_adaptadores/prueba_api.py",
        "utilidades/verificar_reglas.py", "utilidades/preparar_demo.py",
        "utilidades/crear_historial_git.py",
    ]),
    ("Documentar la arquitectura de la Fase 2", ["docs", "README.md", ".gitignore"]),
]


def git(repo, *args):
    resultado = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True
    )
    if resultado.returncode != 0:
        sys.exit(f"git {' '.join(args)} fallo:\n{resultado.stderr}")
    return resultado.stdout


def copiar(origen, destino):
    if os.path.isdir(origen):
        shutil.copytree(
            origen, destino, dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.db", "configuracion.h"),
        )
    else:
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        shutil.copy2(origen, destino)


def app_sin_dispositivos(texto: str) -> str:
    """El app.py del paso 3: todavia no conoce a los dispositivos."""
    texto = texto.replace(
        "from adaptadores.entrada import api_dispositivos, api_front",
        "from adaptadores.entrada import api_front",
    )
    texto = texto.replace(
        "from dominio.servicios.registrar_lectura import RegistrarLectura\n", ""
    )
    return re.sub(
        r"    app\.register_blueprint\(\n        api_dispositivos\.crear_blueprint\(.*?\n        \)\n    \)\n",
        "", texto, flags=re.S,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="clon del repositorio con la Fase 1")
    args = parser.parse_args()
    repo = os.path.abspath(args.repo)
    if not os.path.isdir(os.path.join(repo, ".git")):
        sys.exit("--repo debe ser un repositorio de git")
    if git(repo, "status", "--porcelain").strip():
        sys.exit("El repositorio tiene cambios sin guardar; guardalos o descartalos antes.")

    for vieja in CAPAS_VIEJAS:
        ruta = os.path.join(repo, vieja)
        if os.path.isdir(ruta):
            shutil.rmtree(ruta)
        elif os.path.exists(ruta):
            os.remove(ruta)

    hashes = []
    for indice, (mensaje, rutas) in enumerate(COMMITS, start=1):
        for ruta in rutas:
            copiar(os.path.join(RAIZ, ruta), os.path.join(repo, ruta))
        if indice == 3:
            destino = os.path.join(repo, "servidor/app.py")
            with open(destino, encoding="utf-8") as archivo:
                texto = archivo.read()
            with open(destino, "w", encoding="utf-8") as archivo:
                archivo.write(app_sin_dispositivos(texto))
        git(repo, "add", "-A")
        git(repo, "commit", "-m", mensaje)
        hashes.append(git(repo, "rev-parse", "--short", "HEAD").strip())

    dispositivo = hashes[3]
    tocados = git(repo, "show", "--name-only", "--pretty=format:", dispositivo).split()
    del_dominio = [t for t in tocados if t.startswith("servidor/dominio/")]

    print("Commits creados:")
    for hash_corto, (mensaje, _) in zip(hashes, COMMITS):
        print(f"  {hash_corto}  {mensaje}")
    print(f"\nPrueba de cambio (commit {dispositivo}): archivos del dominio modificados = {len(del_dominio)}")
    for archivo in del_dominio:
        print("  " + archivo)
    sys.exit(1 if del_dominio else 0)


if __name__ == "__main__":
    main()
