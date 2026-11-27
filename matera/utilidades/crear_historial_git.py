"""Arma los commits del proyecto en el orden de la prueba de cambio y comprueba que
agregar cada canal de dispositivos (HTTP, WebSocket, MQTT) no toca el dominio.

Desde la raíz de este proyecto, apuntando a tu clon del repositorio:

  python utilidades/crear_historial_git.py --repo ../diagnostico_materas

Usa tu configuración de git. No sube nada: revisa con git log y haz el push tú.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CAPAS_VIEJAS = [
    "servidor/aplicacion", "servidor/infraestructura", "servidor/presentacion", "servidor/ejecutar.py",
    "servidor/dominio", "servidor/pruebas", "servidor/requirements.txt", "interfaz", "README.md",
]

COMMITS = [
    ("Mover la lógica a un dominio con puertos de entrada y de salida",
     ["servidor/__init__.py", "servidor/dominio", "servidor/pruebas"]),
    ("Agregar adaptadores de salida: especies, usuarios, plantas, dispositivos, historial y puntajes",
     ["servidor/adaptadores/__init__.py", "servidor/adaptadores/salida", "datos", "servidor/requirements.txt",
      "servidor/pruebas_adaptadores/__init__.py", "servidor/pruebas_adaptadores/prueba_salida.py"]),
    ("Agregar API del front, seguridad con JWT y punto de composición",
     ["servidor/adaptadores/entrada/__init__.py", "servidor/adaptadores/entrada/api_front.py",
      "servidor/adaptadores/entrada/errores.py", "servidor/adaptadores/entrada/esquemas.py",
      "servidor/adaptadores/entrada/seguridad.py", "servidor/app.py"]),
    ("Agregar adaptador HTTP de dispositivos y simulador del ESP32",
     ["servidor/adaptadores/entrada/api_dispositivos.py", "servidor/app.py", "simulador",
      "utilidades/preparar_demo.py", "utilidades/generar_id_dispositivo.py"]),
    ("Agregar canal WebSocket para los dispositivos",
     ["servidor/adaptadores/entrada/ws_dispositivos.py", "servidor/adaptadores/entrada/mensajes_dispositivo.py",
      "servidor/app.py", "servidor/requirements.txt"]),
    ("Agregar canal MQTT para los dispositivos",
     ["servidor/adaptadores/entrada/mqtt_dispositivos.py", "servidor/app.py", "servidor/requirements.txt",
      "servidor/requirements-desarrollo.txt", "utilidades/broker_local.py", "broker"]),
    ("Agregar front que se actualiza solo", ["interfaz"]),
    ("Agregar firmware del ESP32 con potenciómetros y pantalla OLED", ["firmware_esp32"]),
    ("Agregar pruebas de los adaptadores y verificación de las reglas",
     ["servidor/pruebas_adaptadores", "utilidades/verificar_reglas.py", "utilidades/crear_historial_git.py"]),
    ("Documentar cómo correr el proyecto", ["README.md", ".gitignore"]),
]
PRUEBAS_DE_CAMBIO = (("HTTP y simulador", 4), ("WebSocket", 5), ("MQTT", 6))


def git(repo, *args):
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"git {' '.join(args)} falló:\n{r.stderr}")
    return r.stdout


def copiar(origen, destino):
    if os.path.isdir(origen):
        shutil.copytree(origen, destino, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.db", "configuracion.h", ".token_*"))
    else:
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        shutil.copy2(origen, destino)


def sin_mqtt(texto):
    texto = texto.replace("api_front, mqtt_dispositivos, ws_dispositivos", "api_front, ws_dispositivos")
    texto = texto.replace(", reloj=None, mqtt=None)", ", reloj=None)")
    return re.sub(r"\n    destino = mqtt or .*?app\.extensions\[\"mqtt\"\] = cliente\n", "\n", texto, flags=re.S)


def sin_websocket(texto):
    texto = sin_mqtt(texto).replace("api_front, ws_dispositivos", "api_front")
    return texto.replace("    ws_dispositivos.registrar(app, seguridad, registrar_lectura, emparejar)\n", "")


def sin_dispositivos(texto):
    texto = sin_websocket(texto).replace("api_dispositivos, api_front", "api_front")
    return texto.replace("    app.register_blueprint(api_dispositivos.crear_blueprint(seguridad, registrar_lectura, emparejar))\n", "")


APP_POR_COMMIT = {3: sin_dispositivos, 4: sin_websocket, 5: sin_mqtt}
REQUISITOS_POR_COMMIT = {2: 3, 3: 3, 4: 3, 5: 5}  # cuántas líneas de requirements.txt existen en ese commit


def transformar(repo, ruta, funcion):
    destino = os.path.join(repo, ruta)
    with open(destino, encoding="utf-8") as f:
        texto = f.read()
    with open(destino, "w", encoding="utf-8") as f:
        f.write(funcion(texto))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    repo = os.path.abspath(parser.parse_args().repo)
    if not os.path.isdir(os.path.join(repo, ".git")):
        sys.exit("--repo debe ser un repositorio de git")
    if git(repo, "status", "--porcelain").strip():
        sys.exit("El repositorio tiene cambios sin guardar; guárdalos o descártalos antes.")

    for vieja in CAPAS_VIEJAS:
        ruta = os.path.join(repo, vieja)
        shutil.rmtree(ruta) if os.path.isdir(ruta) else os.path.exists(ruta) and os.remove(ruta)

    hashes = []
    for n, (mensaje, rutas) in enumerate(COMMITS, start=1):
        for ruta in rutas:
            copiar(os.path.join(RAIZ, ruta), os.path.join(repo, ruta))
        if n in APP_POR_COMMIT:
            transformar(repo, "servidor/app.py", APP_POR_COMMIT[n])
        if n in REQUISITOS_POR_COMMIT:
            transformar(repo, "servidor/requirements.txt",
                        lambda t, k=REQUISITOS_POR_COMMIT[n]: "\n".join(t.splitlines()[:k]) + "\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-m", mensaje)
        hashes.append(git(repo, "rev-parse", "--short", "HEAD").strip())

    print("Commits creados:")
    for h, (mensaje, _) in zip(hashes, COMMITS):
        print(f"  {h}  {mensaje}")
    print()

    del_dominio = []
    for etiqueta, n in PRUEBAS_DE_CAMBIO:
        h = hashes[n - 1]
        tocados = git(repo, "show", "--name-only", "--pretty=format:", h).split()
        dominio = [t for t in tocados if t.startswith("servidor/dominio/")]
        del_dominio += dominio
        print(f"Prueba de cambio ({etiqueta}, commit {h}): archivos del dominio modificados = {len(dominio)}")
    for archivo in del_dominio:
        print("  " + archivo)
    sys.exit(1 if del_dominio else 0)


if __name__ == "__main__":
    main()
