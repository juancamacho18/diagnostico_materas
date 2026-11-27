/*
  Matera - firmware del ESP32

  Tres potenciómetros (humedad, luz, temperatura) y una pantalla OLED con carita según el
  estado que diagnostica el servidor. Envía una lectura cada INTERVALO_MS por el canal que se
  elija en configuracion.h (TRANSPORTE_WEBSOCKET, TRANSPORTE_MQTT o TRANSPORTE_HTTP).

  Sesión del dispositivo: lo único propio es DISPOSITIVO_ID. Cuando el usuario registra la
  matera con ese código, el ESP32 lo presenta, recibe su token una sola vez y lo guarda en la
  flash. Si el dueño pulsa Reemparejar, el servidor rechaza el token y el ESP32 pide otro solo.

  Cableado (potenciómetro: extremos a 3V3 y GND, centro al pin; nunca a 5 V):
    Humedad GPIO32 · Luz GPIO33 · Temperatura GPIO34   (ADC1, sirven con el Wi-Fi encendido)
    OLED SSD1306: VCC 3V3 · GND GND · SDA GPIO21 · SCL GPIO22

  Bibliotecas (Gestor de bibliotecas):
    "WebSockets" de Markus Sattler (2.3 o mayor) · "PubSubClient" de Nick O'Leary
    "Adafruit SSD1306" y "Adafruit GFX"
*/

#define TRANSPORTE_WEBSOCKET 1
#define TRANSPORTE_HTTP 2
#define TRANSPORTE_MQTT 3

#include "configuracion.h"

#ifndef TRANSPORTE
#define TRANSPORTE TRANSPORTE_WEBSOCKET
#endif
#ifndef USAR_OLED
#define USAR_OLED 1
#endif
#ifndef MQTT_USUARIO
#define MQTT_USUARIO ""
#define MQTT_CLAVE ""
#endif

#include "comun.h"

#if TRANSPORTE == TRANSPORTE_WEBSOCKET
#include "transporte_ws.h"
#elif TRANSPORTE == TRANSPORTE_MQTT
#include "transporte_mqtt.h"
#else
#include "transporte_http.h"
#endif

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);
#if USAR_OLED
  pantallaIniciar();
#endif
  memoria.begin("matera", false);
  dispositivoId = DISPOSITIVO_ID;
  token = memoria.getString("token", "");
  Serial.printf("Dispositivo: %s\n", dispositivoId.c_str());
  refrescarPantalla();
  if (conectarWifi()) sincronizarReloj();
  transporteIniciar();
}

void loop() {
  refrescarPantalla();
  if (WiFi.status() != WL_CONNECTED) {
    conectarWifi();
    return;
  }
  transporteBucle();
}
