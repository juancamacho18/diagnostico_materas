import os
from datetime import timedelta
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

from adaptadores.entrada import api_dispositivos, api_front, mqtt_dispositivos, ws_dispositivos
from adaptadores.entrada.errores import ErrorDeEntrada, cuerpo_de_error, describir
from adaptadores.entrada.seguridad import Seguridad
from adaptadores.salida.bd import BaseDatos
from adaptadores.salida.especies import EspeciesBd, EspeciesCsv
from adaptadores.salida.repositorios_bd import (
    DispositivosBd, HistorialBd, PlantasBd, PuntajesBd, UsuariosBd,
)
from adaptadores.salida.seguridad_salida import EmisorJwt, Hasheador, RelojSistema
from dominio.casos_de_uso.cuentas import (
    IniciarSesion, ListarPlantas, RegistrarPlanta, RegistrarUsuario,
)
from dominio.casos_de_uso.diagnostico import Diagnosticar, ListarEspecies
from dominio.casos_de_uso.dispositivos import (
    EmparejarDispositivo, ReemparejarDispositivo, ValidarCredencialDispositivo,
)
from dominio.casos_de_uso.lecturas import (
    AcumularPuntaje, ConsultarEstado, ConsultarHistorial, RegistrarLectura,
)

RAIZ = Path(__file__).resolve().parent
RUTA_ESPECIES = RAIZ.parent / "datos" / "especies.csv"


def crear_app(tipo_tabla=None, ruta_bd=None, secreto=None, reloj=None, mqtt=None) -> Flask:
    tipo_tabla = tipo_tabla or os.environ.get("MATERA_TABLA", "csv")
    ruta_bd = ruta_bd or os.environ.get("MATERA_BD", str(RAIZ / "matera.db"))
    secreto = secreto or os.environ.get("MATERA_SECRETO", "cambia-este-secreto-de-desarrollo-32+")
    periodo = timedelta(seconds=float(os.environ.get("MATERA_PERIODO_PUNTOS", 300)))
    reloj = reloj or RelojSistema()

    # Salida
    bd = BaseDatos(ruta_bd)
    csv_especies = EspeciesCsv(str(RUTA_ESPECIES))
    especies = EspeciesBd(bd, csv_especies) if tipo_tabla == "bd" else csv_especies
    usuarios, plantas, dispositivos = UsuariosBd(bd), PlantasBd(bd), DispositivosBd(bd)
    historial, puntajes = HistorialBd(bd), PuntajesBd(bd)
    emisor, hasheador = EmisorJwt(secreto), Hasheador()

    # Casos de uso
    acumular_puntaje = AcumularPuntaje(puntajes, reloj, periodo)
    registrar_lectura = RegistrarLectura(dispositivos, plantas, especies, historial, acumular_puntaje, reloj)
    emparejar = EmparejarDispositivo(dispositivos, emisor, reloj)
    validar = ValidarCredencialDispositivo(dispositivos)
    seguridad = Seguridad(emisor.verificar, validar.ejecutar)

    # Entrada
    app = Flask(__name__, static_folder=None)
    CORS(app)
    app.register_blueprint(api_front.crear_blueprint(
        seguridad, Diagnosticar(especies), ListarEspecies(especies),
        RegistrarUsuario(usuarios, hasheador), IniciarSesion(usuarios, hasheador, emisor),
        RegistrarPlanta(plantas, dispositivos, especies, reloj), ListarPlantas(plantas, dispositivos),
        ConsultarEstado(plantas, especies, historial, puntajes), ConsultarHistorial(plantas, historial),
        ReemparejarDispositivo(plantas, dispositivos, reloj),
    ))
    app.register_blueprint(api_dispositivos.crear_blueprint(seguridad, registrar_lectura, emparejar))
    ws_dispositivos.registrar(app, seguridad, registrar_lectura, emparejar)

    destino = mqtt or os.environ.get("MATERA_MQTT")
    if destino:
        host, _, puerto = destino.partition(":")
        cliente = mqtt_dispositivos.ClienteMqtt(
            host, int(puerto or 1883), seguridad, registrar_lectura, emparejar,
            os.environ.get("MATERA_MQTT_USUARIO"), os.environ.get("MATERA_MQTT_CLAVE"))
        cliente.iniciar()
        app.extensions["mqtt"] = cliente

    @app.errorhandler(Exception)
    def manejar(error):
        from werkzeug.exceptions import HTTPException
        if isinstance(error, HTTPException):
            return jsonify(cuerpo_de_error(error.name.upper().replace(" ", "_"), error.description)), error.code
        estado, cuerpo = describir(error)
        return jsonify(cuerpo), estado

    return app


if __name__ == "__main__":
    crear_app().run(host="0.0.0.0", port=5000, threaded=True)
