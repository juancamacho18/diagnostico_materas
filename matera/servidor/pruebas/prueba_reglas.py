import unittest

from dominio import reglas
from dominio.errores import ParametroAusente, ValorFueraDeRangoFisico, ValorNoNumerico
from dominio.modelos import Clasificacion, Estado, Medicion, Rango
from pruebas.dobles import MONSTERA


class PruebaClasificar(unittest.TestCase):
    def test_limites_son_optimos(self):
        r = Rango(10, 20)
        self.assertEqual(reglas.clasificar(10, r), Clasificacion.OPTIMO)
        self.assertEqual(reglas.clasificar(20, r), Clasificacion.OPTIMO)
        self.assertEqual(reglas.clasificar(9.9, r), Clasificacion.BAJO)
        self.assertEqual(reglas.clasificar(20.1, r), Clasificacion.ALTO)


class PruebaDiagnostico(unittest.TestCase):
    def diag(self, h, l, t):
        return reglas.diagnosticar(MONSTERA, Medicion(h, l, t))

    def test_saludable(self):
        d = self.diag(60, 3000, 22)
        self.assertEqual(d.estado, Estado.SALUDABLE)
        self.assertEqual(d.recomendaciones, ())

    def test_un_parametro_fuera_es_en_riesgo(self):
        d = self.diag(30, 3000, 22)
        self.assertEqual(d.estado, Estado.EN_RIESGO)
        self.assertEqual(len(d.recomendaciones), 1)

    def test_dos_o_mas_fuera_es_critico(self):
        self.assertEqual(self.diag(30, 100, 22).estado, Estado.CRITICO)
        self.assertEqual(self.diag(30, 100, 50).estado, Estado.CRITICO)

    def test_parametros_en_orden(self):
        d = self.diag(60, 3000, 22)
        self.assertEqual([p.nombre for p in d.parametros], ["humedad", "luz", "temperatura"])


class PruebaValidacion(unittest.TestCase):
    def test_valida(self):
        reglas.validar_medicion(Medicion(0, 0, -20))
        reglas.validar_medicion(Medicion(100, 100000, 60))

    def test_ausente(self):
        with self.assertRaises(ParametroAusente) as c:
            reglas.validar_medicion(Medicion(None, 1, 1))
        self.assertEqual(c.exception.detalle["campo"], "humedad")

    def test_no_numerico(self):
        for malo in ("a", True, [1]):
            with self.assertRaises(ValorNoNumerico):
                reglas.validar_medicion(Medicion(50, malo, 20))

    def test_fuera_de_rango_fisico(self):
        for m in (Medicion(101, 1, 1), Medicion(50, -1, 20), Medicion(50, 100, 61)):
            with self.assertRaises(ValorFueraDeRangoFisico):
                reglas.validar_medicion(m)


if __name__ == "__main__":
    unittest.main()
