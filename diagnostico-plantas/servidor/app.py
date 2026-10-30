"""Punto de composicion: el unico lugar donde se decide que adaptador
se conecta a que puerto. Nada mas en el proyecto instancia adaptadores.

Configuracion por variables de entorno:
  MATERA_TABLA    csv (por defecto) o bd  -> de donde sale la tabla de referencia
  MATERA_BD       ruta del archivo SQLite (por defecto matera.db)
  MATERA_SECRETO  clave con la que se firman los JWT
"""

import os

from flask import Flask
from flask_cors import CORS

from adaptadores.entrada import api_dispositivos, api_front
from adaptadores.entrada.errores import registrar_manejadores
from adaptadores.entrada.seguridad import Seguridad
from adaptadores.salida import bd
from adaptadores.salida.cuentas_bd import PlantasBD, UsuariosBD
from adaptadores.salida.dispositivos_bd import DispositivosBD
from adaptadores.salida.emisor_jwt import EmisorJWT
from adaptadores.salida.hasheador import HasheadorWerkzeug
from adaptadores.salida.historial_bd import HistorialBD
from adaptadores.salida.tabla_bd import TablaBD
from adaptadores.salida.tabla_csv import TablaCSV
from dominio.evaluador import (
    EvaluadorDeEstadoGlobal,
    EvaluadorHumedad,
    EvaluadorLuz,
    EvaluadorTemperatura,
    GeneradorDeRecomendaciones,
)
from dominio.servicio_diagnostico import ServicioDiagnostico
from dominio.servicios.consultar import ConsultarEstado, ConsultarHistorial, ListarPlantas
from dominio.servicios.cuentas import IniciarSesion, RegistrarPlanta, RegistrarUsuario
from dominio.servicios.diagnosticar_medicion import DiagnosticarMedicion
from dominio.servicios.listar_especies import ListarEspecies
from dominio.servicios.registrar_lectura import RegistrarLectura

_AQUI = os.path.dirname(os.path.abspath(__file__))
_RUTA_CSV = os.path.join(_AQUI, "adaptadores", "salida", "especies.csv")


def crear_app(
    tipo_tabla: str = None, ruta_bd: str = None, secreto: str = None
) -> Flask:
    tipo_tabla = (tipo_tabla or os.environ.get("MATERA_TABLA", "csv")).lower()
    ruta_bd = ruta_bd or os.environ.get("MATERA_BD", os.path.join(_AQUI, "matera.db"))
    secreto = secreto or os.environ.get("MATERA_SECRETO", "secreto-solo-para-desarrollo-cambiar")

    bd.crear_tablas(ruta_bd)

    # Puertos de salida
    tabla_csv = TablaCSV(_RUTA_CSV)
    if tipo_tabla == "bd":
        tabla = TablaBD(ruta_bd)
        if tabla.esta_vacia():
            tabla.cargar(tabla_csv.listar_todas())
    elif tipo_tabla == "csv":
        tabla = tabla_csv
    else:
        raise ValueError(f"MATERA_TABLA debe ser 'csv' o 'bd', no {tipo_tabla!r}")

    historial = HistorialBD(ruta_bd)
    plantas = PlantasBD(ruta_bd)
    dispositivos = DispositivosBD(ruta_bd)
    usuarios = UsuariosBD(ruta_bd)
    hasheador = HasheadorWerkzeug()
    emisor = EmisorJWT(secreto)

    # Dominio
    servicio = ServicioDiagnostico(
        evaluador_humedad=EvaluadorHumedad(),
        evaluador_luz=EvaluadorLuz(),
        evaluador_temperatura=EvaluadorTemperatura(),
        evaluador_estado_global=EvaluadorDeEstadoGlobal(),
        generador_recomendaciones=GeneradorDeRecomendaciones(),
    )

    # Adaptadores de entrada
    seguridad = Seguridad(emisor.verificar)

    app = Flask(__name__)
    CORS(app)  # el front se sirve desde otro origen
    registrar_manejadores(app)

    app.register_blueprint(
        api_front.crear_blueprint(
            seguridad=seguridad,
            diagnosticar=DiagnosticarMedicion(tabla, servicio),
            listar_especies=ListarEspecies(tabla),
            registrar_usuario=RegistrarUsuario(usuarios, hasheador),
            iniciar_sesion=IniciarSesion(usuarios, hasheador, emisor),
            registrar_planta=RegistrarPlanta(plantas, dispositivos, historial, tabla, emisor),
            listar_plantas=ListarPlantas(plantas),
            consultar_estado=ConsultarEstado(plantas, tabla, historial, servicio),
            consultar_historial=ConsultarHistorial(plantas, historial),
        )
    )
    app.register_blueprint(
        api_dispositivos.crear_blueprint(
            seguridad, RegistrarLectura(dispositivos, plantas, tabla, historial, servicio)
        )
    )
    return app


if __name__ == "__main__":
    # 0.0.0.0 para que el ESP32 (otro equipo de la red) pueda llegar.
    crear_app().run(host="0.0.0.0", port=5000, debug=False)
