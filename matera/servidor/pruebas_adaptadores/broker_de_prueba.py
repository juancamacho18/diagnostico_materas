"""Broker MQTT en memoria para las pruebas."""

import asyncio
import socket
import threading

from amqtt.broker import Broker


class BrokerDePrueba:
    def __init__(self):
        with socket.socket() as libre:
            libre.bind(("127.0.0.1", 0))
            self.puerto = libre.getsockname()[1]
        self._config = {
            "listeners": {"default": {"type": "tcp", "bind": f"127.0.0.1:{self.puerto}"}},
            "sys_interval": 0,
            "auth": {"allow-anonymous": True, "plugins": ["auth_anonymous"]},
            "topic-check": {"enabled": False},
        }
        self._listo = threading.Event()
        self._hilo = threading.Thread(target=self._correr, daemon=True)

    def iniciar(self) -> None:
        self._hilo.start()
        if not self._listo.wait(timeout=10):
            raise RuntimeError("el broker de prueba no arranco")

    def detener(self) -> None:
        futuro = asyncio.run_coroutine_threadsafe(self._broker.shutdown(), self._bucle)
        futuro.result(timeout=10)
        self._bucle.call_soon_threadsafe(self._bucle.stop)
        self._hilo.join(timeout=10)

    def _correr(self) -> None:
        self._bucle = asyncio.new_event_loop()
        asyncio.set_event_loop(self._bucle)
        self._broker = Broker(self._config, loop=self._bucle)
        self._bucle.run_until_complete(self._broker.start())
        self._listo.set()
        self._bucle.run_forever()
