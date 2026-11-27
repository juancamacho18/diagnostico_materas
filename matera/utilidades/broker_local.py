"""Broker MQTT para desarrollo, sin instalar nada aparte de la libreria:

  pip install amqtt
  python utilidades/broker_local.py            # escucha en 0.0.0.0:1883

Acepta conexiones sin usuario ni clave: solo para la red del laboratorio.
Para algo mas serio usar Mosquitto con broker/mosquitto.conf.
"""

import argparse
import asyncio
import logging

from amqtt.broker import Broker


async def correr(puerto: int) -> None:
    broker = Broker(
        {
            "listeners": {"default": {"type": "tcp", "bind": f"0.0.0.0:{puerto}"}},
            "sys_interval": 0,
            "auth": {"allow-anonymous": True, "plugins": ["auth_anonymous"]},
            "topic-check": {"enabled": False},
        }
    )
    await broker.start()
    print(f"Broker MQTT escuchando en el puerto {puerto} (Ctrl+C para parar)")
    await asyncio.Event().wait()


def main():
    parser = argparse.ArgumentParser(description="Broker MQTT local")
    parser.add_argument("--puerto", type=int, default=1883)
    args = parser.parse_args()
    logging.getLogger("amqtt").setLevel(logging.WARNING)
    try:
        asyncio.run(correr(args.puerto))
    except KeyboardInterrupt:
        print("\nBroker detenido.")


if __name__ == "__main__":
    main()
