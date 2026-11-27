import unittest
from datetime import timedelta

from dominio.modelos import Estado, Puntaje
from dominio.puntaje import acumular
from pruebas.dobles import INICIO

P = timedelta(seconds=300)


class PruebaPuntaje(unittest.TestCase):
    def test_primera_lectura_no_cobra(self):
        n, v = acumular(Puntaje("A"), Estado.SALUDABLE, INICIO, P)
        self.assertEqual((n.puntos, v), (0, 0))

    def test_un_periodo_saludable_suma(self):
        n, _ = acumular(Puntaje("A"), Estado.SALUDABLE, INICIO, P)
        n, v = acumular(n, Estado.SALUDABLE, INICIO + P, P)
        self.assertEqual((n.puntos, v), (10, 10))

    def test_varios_periodos(self):
        n, _ = acumular(Puntaje("A", 50), Estado.EN_RIESGO, INICIO, P)
        n, v = acumular(n, Estado.EN_RIESGO, INICIO + P * 1.0, P)
        self.assertEqual(v, -5)

    def test_no_baja_de_cero(self):
        n, _ = acumular(Puntaje("A", 3), Estado.CRITICO, INICIO, P)
        n, v = acumular(n, Estado.CRITICO, INICIO + P, P)
        self.assertEqual((n.puntos, v), (0, -3))

    def test_cambio_de_estado_reinicia_racha(self):
        n, _ = acumular(Puntaje("A"), Estado.SALUDABLE, INICIO, P)
        n, v = acumular(n, Estado.CRITICO, INICIO + P, P)
        self.assertEqual((n.puntos, v), (0, 0))

    def test_silencio_largo_reinicia_racha(self):
        n, _ = acumular(Puntaje("A"), Estado.SALUDABLE, INICIO, P)
        n, v = acumular(n, Estado.SALUDABLE, INICIO + P * 3, P)
        self.assertEqual(v, 0)

    def test_cobra_solo_periodos_completos(self):
        n, _ = acumular(Puntaje("A"), Estado.SALUDABLE, INICIO, P)
        n, v = acumular(n, Estado.SALUDABLE, INICIO + timedelta(seconds=299), P)
        self.assertEqual(v, 0)
        n, v = acumular(n, Estado.SALUDABLE, INICIO + timedelta(seconds=310), P)
        self.assertEqual(v, 10)


if __name__ == "__main__":
    unittest.main()
