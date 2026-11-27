# Matera

Matera inteligente: un ESP32 (o su simulador) manda humedad, luz y temperatura; el servidor las compara con el rango de la especie, guarda el historial, lleva los puntos de la planta y el front lo muestra. El ESP32 dibuja en una pantalla OLED una carita según el estado.

Arquitectura hexagonal: el dominio define los puertos y los adaptadores (HTTP, WebSocket, MQTT, SQLite, CSV, JWT) los implementan. `servidor/app.py` es el único lugar donde se arman.

## Estructura

```
servidor/
  dominio/            reglas, modelos, puertos/ y casos_de_uso/ (sin Flask, SQL, CSV, JSON ni JWT)
  adaptadores/
    entrada/          api_front, api_dispositivos, ws_dispositivos, mqtt_dispositivos, seguridad, esquemas, errores
    salida/           bd, repositorios_bd, especies (CSV o BD), seguridad_salida (JWT, hash, reloj)
  app.py              punto de composición
  pruebas/            dominio, con dobles en memoria
  pruebas_adaptadores/
simulador/            simulador_esp32.py (ws | http | mqtt)
firmware_esp32/       código del ESP32: potenciómetros, OLED y los tres canales
interfaz/             front estático
broker/               mosquitto.conf y acl
datos/especies.csv    rangos por especie
utilidades/           preparar_demo, broker_local, verificar_reglas, crear_historial_git, generar_id_dispositivo
```

## Servidor

```bash
cd servidor
pip install -r requirements.txt
python app.py            # 0.0.0.0:5000
```

| Variable | Para qué |
|---|---|
| `MATERA_TABLA` | `csv` (defecto) o `bd`: de dónde salen las especies |
| `MATERA_BD` | archivo SQLite (`servidor/matera.db`) |
| `MATERA_SECRETO` | clave de los JWT, 32 caracteres o más: cámbiala |
| `MATERA_MQTT` | `host:puerto` del broker; sin ella el servidor corre sin MQTT |
| `MATERA_MQTT_USUARIO`, `MATERA_MQTT_CLAVE` | credenciales del broker |
| `MATERA_PERIODO_PUNTOS` | segundos por periodo de puntos (300) |

## Front

```bash
cd interfaz && python -m http.server 8080
```

Abrir `http://127.0.0.1:8080`. Se actualiza cada 5 s. Si el servidor está en otra dirección, define `window.MATERA_API` antes de cargar `logica.js`.

## API

| Ruta | Quién | Para qué |
|---|---|---|
| `GET /api/especies` · `POST /api/diagnostico` | público | rangos y diagnóstico manual |
| `POST /api/usuarios` · `POST /api/sesion` | público | cuenta y token de usuario (1 h) |
| `GET/POST /api/plantas` | usuario | listar y registrar matera con el código del dispositivo |
| `GET /api/plantas/{id}/estado` · `/lecturas?limite=` | dueño | estado, puntos e historial |
| `POST /api/plantas/{id}/reemparejar` | dueño | revoca el token del dispositivo |
| `POST /api/dispositivos/{id}/emparejar` | dispositivo | entrega el token, una sola vez |
| `POST /api/dispositivos/{id}/lecturas` | dispositivo | lectura (token en `Authorization: Bearer`) |
| `WS /ws/dispositivos` | dispositivo | `emparejar` → `autenticar` → `lectura` |
| MQTT `matera/{id}/emparejar · lectura · respuesta` | dispositivo / servidor | mismo flujo; el token va en la carga, nunca en el tema |

Errores: `{"error", "mensaje", "detalle"}` con 400 (dato ausente o no numérico), 401 (token), 403, 404, 409, 422 (fuera del rango físico).

## Tokens

- **Usuario**: se obtiene con correo y clave; dura 1 hora.
- **Dispositivo**: el ESP32 solo lleva su código (`ESP32-` + 12 hex). Al registrar la matera, el dispositivo queda PENDIENTE 10 minutos; en ese lapso pide su token, que se entrega una sola vez y el ESP32 guarda en su flash. El servidor no guarda tokens, solo un contador de generación: **Reemparejar** lo sube y el token viejo deja de servir; el dispositivo pide otro solo.
- Los JWT se verifican en el adaptador de entrada (`seguridad.py`); que una planta sea de su usuario lo decide el dominio.
- En WebSocket el token se presenta una vez por conexión y se vuelve a verificar en cada lectura. En MQTT va en cada lectura, debe ser del mismo dispositivo que el tema y nada se publica con `retain`.

## Simulador

```bash
python utilidades/generar_id_dispositivo.py                       # ESP32-XXXXXXXXXXXX
python utilidades/preparar_demo.py --dispositivo ESP32-XXXXXXXXXXXX
python simulador/simulador_esp32.py --dispositivo ESP32-XXXXXXXXXXXX --transporte ws --intervalo 3
```

`--transporte ws|http|mqtt`, `--fuera-de-rango`, `--invalidas`, `--ciclos`, `--semilla`. Para MQTT: `pip install -r servidor/requirements-desarrollo.txt`, `python utilidades/broker_local.py`, servidor con `MATERA_MQTT=127.0.0.1:1883` y `--transporte mqtt`. Usuario de demostración: `demo@matera.com` / `demo123`.

## Puntos y carita

Mientras la planta sigue en el mismo estado, cada periodo completo suma o resta: SALUDABLE +10, EN_RIESGO −5, CRITICO −10 (mínimo 0). Si el estado cambia o el dispositivo calla más de un periodo, la racha vuelve a empezar. Para probar rápido: `MATERA_PERIODO_PUNTOS=10`.

## ESP32 real

Hardware: ESP32, 3 potenciómetros (humedad GPIO32, luz GPIO33, temperatura GPIO34; extremos a 3V3 y GND) y pantalla OLED SSD1306 128×64 I2C (VCC 3V3, GND, SDA GPIO21, SCL GPIO22, dirección 0x3C).

1. Arduino IDE con soporte ESP32. Bibliotecas: **WebSockets** (Markus Sattler), **PubSubClient** (Nick O'Leary), **Adafruit SSD1306** y **Adafruit GFX**.
2. Copiar `configuracion.h.ejemplo` a `configuracion.h` y llenar Wi-Fi, IP del PC, `DISPOSITIVO_ID` (generado con la utilidad) y `TRANSPORTE`.
3. Registrar la matera en el front con ese código y, dentro de los 10 minutos, encender el ESP32 (monitor serie a 115200).
4. Con MQTT en Mosquitto: `broker/mosquitto.conf` y `broker/acl`; el servidor entra como `servidor` y los ESP32 como `dispositivos` (`MQTT_USUARIO`/`MQTT_CLAVE` en la configuración).

Caritas: feliz (SALUDABLE), preocupada (EN_RIESGO), triste (CRITICO), tres círculos mientras espera, dormida sin red.

## Pruebas

```bash
cd servidor
python -m unittest discover -s pruebas -t . -p "prueba_*.py"               # dominio
python -m unittest discover -s pruebas_adaptadores -t . -p "prueba_*.py"   # adaptadores (necesita requirements-desarrollo.txt)
python ../utilidades/verificar_reglas.py
```

## Prueba de cambio

`python utilidades/crear_historial_git.py --repo ../tu-clon` arma los commits en orden. Agregar el adaptador HTTP de dispositivos, el WebSocket y MQTT modifica solo un adaptador nuevo, `app.py` y `requirements.txt`: ningún archivo de `servidor/dominio/`. El script lo comprueba.
