from dominio import reglas
from dominio.errores import EspecieDesconocida
from dominio.modelos import Diagnostico, Medicion
from dominio.puertos.salida import EspecieRepositorioPuerto


class Diagnosticar:
    def __init__(self, especies: EspecieRepositorioPuerto):
        self._especies = especies

    def ejecutar(self, especie: str, medicion: Medicion) -> Diagnostico:
        reglas.validar_medicion(medicion)
        datos = self._especies.obtener(especie)
        if datos is None:
            raise EspecieDesconocida(f"Especie desconocida: {especie}", {"especie": especie})
        return reglas.diagnosticar(datos, medicion)


class ListarEspecies:
    def __init__(self, especies: EspecieRepositorioPuerto):
        self._especies = especies

    def ejecutar(self) -> list:
        return self._especies.listar()
