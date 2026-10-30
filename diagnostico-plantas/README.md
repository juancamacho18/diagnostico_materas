# Proyecto Matera · Fase 2

Lecturas de humedad, luz y temperatura que llegan desde un ESP32 (o un simulador) se comparan con el rango de la especie de cada matera y se guardan en un historial. Cada matera pertenece a un usuario. Back con arquitectura hexagonal (puertos y adaptadores) y front estático separado.

## Estructura

```
diagnostico-plantas/
├── servidor/
│   ├── dominio/                 # reglas de negocio, sin Flask/CSV/SQL/JSON/JWT
│   │   ├── entidades.py  validacion.py  especie.py  excepciones.py
│   │   ├── evaluador.py  servicio_diagnostico.py
│   │   ├── puertos/             # entrada.py (lo que ofrece) · salida.py (lo que necesita)
│   │   └── servicios/           # casos de uso que cumplen los puertos de entrada
│   ├── adaptadores/
│   │   ├── entrada/             # api_front.py · api_dispositivos.py · seguridad.py · dtos.py · errores.py
│   │   └── salida/              # tabla_csv.py · tabla_bd.py · historial_bd.py · cuentas_bd.py
│   │                            # dispositivos_bd.py · bd.py · emisor_jwt.py · hasheador.py
│   ├── app.py                   # único punto de composición
│   ├── pruebas/                 # dominio, con dobles en memoria
│   └── pruebas_adaptadores/     # API, BD, CSV y JWT
├── simulador/simulador_esp32.py # simula el dispositivo
├── firmware_esp32/              # código del ESP32 real con 3 potenciómetros
├── interfaz/                    # front estático
├── utilidades/                  # preparar_demo, verificar_reglas, crear_historial_git
├── docs/                        # arquitectura (4 páginas), diagrama y bitácora
└── datos_originales/
```

## Base de datos

SQLite, un archivo (`servidor/matera.db`) que se crea solo.

| Tabla | Contenido |
|---|---|
| `usuarios` | id, correo, hash de la clave |
| `especies` | rangos de humedad, luz y temperatura por especie (se llena desde el CSV) |
| `plantas` | id `MAT-XXXXXX`, nombre, especie, usuario dueño |
| `dispositivos` | id del dispositivo y la planta a la que pertenece |
| `lecturas_MAT_XXXXXX` | una tabla por planta: momento, humedad, luz, temperatura, estado |

## Correr el back

```bash
cd servidor
pip install -r requirements.txt
python app.py
```

Escucha en `0.0.0.0:5000` para que el ESP32 pueda llegar desde la red. Variables de entorno:

| Variable | Valores | Para qué |
|---|---|---|
| `MATERA_TABLA` | `csv` (defecto) o `bd` | de dónde sale la tabla de especies |
| `MATERA_BD` | ruta | archivo SQLite |
| `MATERA_SECRETO` | texto de 32 caracteres o más | clave con la que se firman los JWT (cámbiala) |

## Correr el front

```bash
cd interfaz
python -m http.server 8080
```

Abrir `http://127.0.0.1:8080`. Se actualiza solo cada 5 segundos.

## Correr el simulador

Con el back corriendo:

```bash
python utilidades/preparar_demo.py --dispositivo ESP32-A3F2    # crea usuario y matera, imprime el token del dispositivo
python simulador/simulador_esp32.py --dispositivo ESP32-A3F2 --token <TOKEN> --intervalo 3
```

Usuario de demostración: `demo@matera.com` / `demo123`. El simulador manda lecturas normales, fuera de rango e inválidas; se configuran con `--fuera-de-rango`, `--invalidas`, `--ciclos` y `--semilla`.

## Conectar el ESP32 físico

1. Montar los tres potenciómetros como en `firmware_esp32/cableado.png`: extremos a 3V3 y GND, pin central a GPIO32 (humedad), GPIO33 (luz) y GPIO34 (temperatura). Nunca a 5 V.
2. Copiar `firmware_esp32/configuracion.h.ejemplo` como `configuracion.h` y llenar Wi-Fi, IP del PC, id del dispositivo y el token que imprime `preparar_demo.py`.
3. Abrir `firmware_esp32.ino` en Arduino IDE (placa ESP32), cargar y abrir el monitor serie a 115200.
4. El PC y el ESP32 deben estar en la misma red. Si el monitor muestra `201`, la lectura llegó.

## API

| Ruta | Quién | Qué hace |
|---|---|---|
| `POST /api/dispositivos/{id}/lecturas` | dispositivo (JWT de dispositivo) | reporta una lectura: dispositivo, `marcaTiempo` (ISO 8601, opcional) y los tres valores |
| `POST /api/v1/auth/registro`, `/auth/login` | público | crear cuenta y obtener JWT de usuario |
| `POST /api/v1/plantas` | usuario | registra una matera y devuelve el token de su dispositivo |
| `GET /api/v1/plantas` | usuario | lista sus materas |
| `GET /api/v1/plantas/{id}/estado` y `/historial?limite=` | usuario dueño | estado actual e historial |
| `GET /api/v1/especies` y `POST /api/v1/diagnosticos` | público | catálogo y diagnóstico suelto (Fase 1) |

Todos los errores salen como `{ "error", "mensaje", "detalle" }`.

## Pruebas

```bash
cd servidor
python -m unittest discover -s pruebas -t . -p "prueba_*.py" -v              # dominio, sin servidor, archivos ni BD
python -m unittest discover -s pruebas_adaptadores -t . -p "prueba_*.py" -v  # API, BD, CSV y JWT
cd ..
python utilidades/verificar_reglas.py                                         # reglas no negociables
```

## Prueba de cambio

`python utilidades/crear_historial_git.py --repo <tu clon>` arma los commits en orden y falla si el commit del dispositivo y el simulador toca algún archivo de `servidor/dominio/`.

## Documentación

- `docs/arquitectura.md`: documento de arquitectura (diagrama, puertos, JWT, SOLID, prueba de cambio, MQTT).
- `docs/bitacora_fase2.md`: uso de IA en la fase.
