"""Reglas de clasificacion de parametros, agregacion del estado
global y generacion de recomendaciones."""

from abc import ABC, abstractmethod
from typing import List

from dominio.entidades import EstadoParametro, EstadoPlanta, ParametroEvaluado
from dominio.especie import Especie, RangoOptimo


class ClasificadorDeRango:
    """Clasifica un numero contra un rango. La usan los tres
    evaluadores de parametro para no repetir el mismo if/else."""

    @staticmethod
    def clasificar(valor: float, rango: RangoOptimo) -> EstadoParametro:
        if valor < rango.minimo:
            return EstadoParametro.BAJO
        if valor > rango.maximo:
            return EstadoParametro.ALTO
        return EstadoParametro.OPTIMO


class IEvaluadorDeParametro(ABC):
    @abstractmethod
    def evaluar(self, especie: Especie, valor: float) -> ParametroEvaluado:
        raise NotImplementedError


class EvaluadorHumedad(IEvaluadorDeParametro):
    def evaluar(self, especie: Especie, valor: float) -> ParametroEvaluado:
        estado = ClasificadorDeRango.clasificar(valor, especie.humedad)
        return ParametroEvaluado("humedad", valor, "%", especie.humedad, estado)


class EvaluadorLuz(IEvaluadorDeParametro):
    def evaluar(self, especie: Especie, valor: float) -> ParametroEvaluado:
        estado = ClasificadorDeRango.clasificar(valor, especie.luz)
        return ParametroEvaluado("luz", valor, "lux", especie.luz, estado)


class EvaluadorTemperatura(IEvaluadorDeParametro):
    def evaluar(self, especie: Especie, valor: float) -> ParametroEvaluado:
        estado = ClasificadorDeRango.clasificar(valor, especie.temperatura)
        return ParametroEvaluado("temperatura", valor, "C", especie.temperatura, estado)


class EvaluadorDeEstadoGlobal:
    """
    Deriva el estado global de la planta a partir de los 3 estados
    individuales:
      - 0 parametros fuera de rango -> SALUDABLE
      - 1 parametro fuera de rango  -> EN_RIESGO
      - 2 o mas fuera de rango      -> CRITICO

    Se eligio un conteo simple en vez de ponderar (por ejemplo,
    humedad mas que luz) porque con solo 3 parametros y sin datos
    historicos no habria como justificar los pesos.
    """

    def calcular(self, parametros: List[ParametroEvaluado]) -> EstadoPlanta:
        fuera_de_rango = sum(
            1 for p in parametros if p.estado != EstadoParametro.OPTIMO
        )
        if fuera_de_rango == 0:
            return EstadoPlanta.SALUDABLE
        if fuera_de_rango == 1:
            return EstadoPlanta.EN_RIESGO
        return EstadoPlanta.CRITICO


class GeneradorDeRecomendaciones:
    _MENSAJES = {
        ("humedad", EstadoParametro.BAJO):
            "La humedad del sustrato esta por debajo del rango recomendado: riegue moderadamente.",
        ("humedad", EstadoParametro.ALTO):
            "La humedad del sustrato esta por encima del rango recomendado: reduzca el riego y mejore el drenaje.",
        ("luz", EstadoParametro.BAJO):
            "La planta esta recibiendo menos luz de la recomendada: acerquela a una fuente de luz o a una ventana.",
        ("luz", EstadoParametro.ALTO):
            "La planta esta recibiendo mas luz de la recomendada: alejela de la luz directa o proporcione sombra parcial.",
        ("temperatura", EstadoParametro.BAJO):
            "La temperatura esta por debajo del rango recomendado: reubique la planta en un sitio mas calido.",
        ("temperatura", EstadoParametro.ALTO):
            "La temperatura esta por encima del rango recomendado: reubique la planta en un sitio mas fresco o ventilado.",
    }

    def generar(self, parametros: List[ParametroEvaluado]) -> List[str]:
        recomendaciones = []
        for p in parametros:
            if p.estado == EstadoParametro.OPTIMO:
                continue
            mensaje = self._MENSAJES.get((p.nombre, p.estado))
            if mensaje:
                recomendaciones.append(mensaje)
        return recomendaciones
