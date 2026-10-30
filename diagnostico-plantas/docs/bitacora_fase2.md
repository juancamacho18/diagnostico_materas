# Bitácora de la Fase 2

Registro de cómo se usó la IA en esta fase. Completar o corregir lo que el equipo recuerde distinto.

| Fecha | Tarea | Qué se pidió | Qué se hizo con la respuesta | Verificación |
|---|---|---|---|---|
| 2026-10-21 | Pantallas | Maquetas simples de login, registro de matera, "Mis materas" y búsqueda | Se usaron como guía del front; la búsqueda de plantas ajenas se descartó por R7 | Revisadas por el equipo |
| 2026-10-21 | Plan | Plan para pasar de capas a hexagonal, con JWT | Se adoptó el orden: primero reestructurar, luego dispositivo, luego seguridad | Contrastado con el enunciado |
| 2026-10-22 | Explicación | Qué es cada pieza (dominio, puertos, adaptadores, JWT, composición) | Base de la presentación al profesor | Revisado con el código |
| 2026-10-26 | Cableado | Diagrama de 3 potenciómetros al ESP32 | Pendiente de montar | Pendiente en hardware |
| 2026-10-26 | Esqueleto | Servidor hexagonal, simulador, firmware y front | Código base del repositorio | 36 pruebas del dominio, simulador de punta a punta |
| 2026-10-26 | Pruebas y ajustes | Pruebas de API, BD y JWT | Las pruebas encontraron dos fallos que se corrigieron: conexiones SQLite sin cerrar y orden distinto entre CSV y BD | 46 pruebas de adaptadores |
| 2026-10-27 | Aclaración de responsabilidades | Qué va en el dominio, en puertos y en adaptadores; validación en el dominio; una tabla de lecturas por planta; tabla de dispositivos | Se movió la validación física de la lectura al dominio y se agregaron `Dispositivo` y su puerto | Pruebas del dominio con dobles |

## Pendiente de verificar a mano

- Compilar y cargar el firmware en el ESP32 real.
- Confirmar con el profesor el uso de C++ en el firmware.
