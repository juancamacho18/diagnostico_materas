"""Orquesta los evaluadores para producir un Diagnostico completo a
partir de una Especie y una Medicion ya validadas."""

from dominio.entidades import Diagnostico, Medicion
from dominio.especie import Especie
from dominio.evaluador import (
    EvaluadorDeEstadoGlobal,
    GeneradorDeRecomendaciones,
    IEvaluadorDeParametro,
)


class ServicioDiagnostico:
    def __init__(
        self,
        evaluador_humedad: IEvaluadorDeParametro,
        evaluador_luz: IEvaluadorDeParametro,
        evaluador_temperatura: IEvaluadorDeParametro,
        evaluador_estado_global: EvaluadorDeEstadoGlobal,
        generador_recomendaciones: GeneradorDeRecomendaciones,
    ):
        self._evaluador_humedad = evaluador_humedad
        self._evaluador_luz = evaluador_luz
        self._evaluador_temperatura = evaluador_temperatura
        self._evaluador_estado_global = evaluador_estado_global
        self._generador_recomendaciones = generador_recomendaciones

    def diagnosticar(self, especie: Especie, medicion: Medicion) -> Diagnostico:
        parametros = [
            self._evaluador_humedad.evaluar(especie, medicion.humedad),
            self._evaluador_luz.evaluar(especie, medicion.luz),
            self._evaluador_temperatura.evaluar(especie, medicion.temperatura),
        ]
        estado = self._evaluador_estado_global.calcular(parametros)
        recomendaciones = self._generador_recomendaciones.generar(parametros)
        return Diagnostico(
            especie=especie.nombre,
            estado=estado,
            parametros=parametros,
            recomendaciones=recomendaciones,
        )
