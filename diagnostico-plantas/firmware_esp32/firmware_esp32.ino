/*
  Matera - firmware del ESP32

  Lee tres potenciometros (humedad, luz y temperatura) y manda una
  lectura al servidor cada INTERVALO_MS por Wi-Fi. Cada lectura lleva
  el dispositivo, la marca de tiempo (hora UTC por NTP) y los tres
  valores, con el token del dispositivo.

  Conexiones (cada potenciometro: un extremo a 3V3, el otro a GND y
  el pin del medio a su GPIO):
    Humedad      -> GPIO32
    Luz          -> GPIO33
    Temperatura  -> GPIO34
  Son pines ADC1: los ADC2 no funcionan con el Wi-Fi encendido.
  Nunca conectar un potenciometro a 5 V.
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <time.h>
#include "configuracion.h"

const int PIN_HUMEDAD = 32;
const int PIN_LUZ = 33;
const int PIN_TEMPERATURA = 34;

const float HUMEDAD_MIN = 0.0,      HUMEDAD_MAX = 100.0;    // %
const float LUZ_MIN = 0.0,          LUZ_MAX = 20000.0;      // lux
const float TEMPERATURA_MIN = 0.0,  TEMPERATURA_MAX = 45.0; // C

const int MUESTRAS = 16;
const unsigned long ESPERA_WIFI_MS = 15000;
const int TIEMPO_LIMITE_HTTP_MS = 5000;
const time_t HORA_MINIMA_VALIDA = 1700000000;  // si el reloj marca menos, no se sincronizo

float leerPromedio(int pin) {
  long suma = 0;
  for (int i = 0; i < MUESTRAS; i++) {
    suma += analogRead(pin);
    delay(2);
  }
  return suma / (float)MUESTRAS;
}

float escalar(float crudo, float minimo, float maximo) {
  return minimo + (crudo / 4095.0f) * (maximo - minimo);
}

bool conectarWifi() {
  if (WiFi.status() == WL_CONNECTED) return true;

  Serial.printf("Conectando a %s", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_CLAVE);

  unsigned long inicio = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - inicio < ESPERA_WIFI_MS) {
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("\nNo hubo conexion Wi-Fi. Se reintenta en la proxima lectura.");
    return false;
  }
  Serial.printf("\nConectado. IP del ESP32: %s\n", WiFi.localIP().toString().c_str());
  return true;
}

// Hora UTC en formato ISO 8601. Devuelve false si el reloj no esta sincronizado.
bool marcaDeTiempo(char *destino, size_t largo) {
  time_t ahora = time(nullptr);
  if (ahora < HORA_MINIMA_VALIDA) return false;
  struct tm fecha;
  gmtime_r(&ahora, &fecha);
  strftime(destino, largo, "%Y-%m-%dT%H:%M:%SZ", &fecha);
  return true;
}

void sincronizarReloj() {
  configTime(0, 0, "pool.ntp.org", "time.google.com");
  unsigned long inicio = millis();
  while (time(nullptr) < HORA_MINIMA_VALIDA && millis() - inicio < ESPERA_WIFI_MS) {
    delay(250);
  }
  Serial.println(time(nullptr) < HORA_MINIMA_VALIDA
                     ? "Reloj sin sincronizar: el servidor pondra la hora."
                     : "Reloj sincronizado.");
}

void explicarCodigo(int codigo) {
  if (codigo == 401) Serial.println("  -> Token invalido o vencido: genera otro con preparar_demo.py");
  else if (codigo == 403) Serial.println("  -> El token no corresponde a DISPOSITIVO_ID");
  else if (codigo == 404) Serial.println("  -> Ese dispositivo no esta registrado en ninguna matera");
  else if (codigo == 400) Serial.println("  -> El servidor rechazo los valores");
}

void enviarLectura(float humedad, float luz, float temperatura) {
  if (!conectarWifi()) return;

  String url = String(SERVIDOR) + "/api/dispositivos/" + DISPOSITIVO_ID + "/lecturas";

  char marca[24];
  char cuerpo[192];
  if (marcaDeTiempo(marca, sizeof(marca))) {
    snprintf(cuerpo, sizeof(cuerpo),
             "{\"dispositivo\":\"%s\",\"marcaTiempo\":\"%s\",\"humedad\":%.1f,\"luz\":%.0f,\"temperatura\":%.1f}",
             DISPOSITIVO_ID, marca, humedad, luz, temperatura);
  } else {
    snprintf(cuerpo, sizeof(cuerpo),
             "{\"dispositivo\":\"%s\",\"humedad\":%.1f,\"luz\":%.0f,\"temperatura\":%.1f}",
             DISPOSITIVO_ID, humedad, luz, temperatura);
  }

  HTTPClient http;
  http.setTimeout(TIEMPO_LIMITE_HTTP_MS);
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", String("Bearer ") + TOKEN_DISPOSITIVO);

  int codigo = http.POST(cuerpo);
  if (codigo > 0) {
    Serial.printf("POST %s -> %d %s\n", cuerpo, codigo, http.getString().c_str());
    explicarCodigo(codigo);
  } else {
    Serial.printf("No se pudo enviar: %s\n", http.errorToString(codigo).c_str());
  }
  http.end();
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);
  if (conectarWifi()) sincronizarReloj();
}

void loop() {
  unsigned long inicio = millis();

  float humedad = escalar(leerPromedio(PIN_HUMEDAD), HUMEDAD_MIN, HUMEDAD_MAX);
  float luz = escalar(leerPromedio(PIN_LUZ), LUZ_MIN, LUZ_MAX);
  float temperatura = escalar(leerPromedio(PIN_TEMPERATURA), TEMPERATURA_MIN, TEMPERATURA_MAX);

  Serial.printf("Humedad %.1f %% | Luz %.0f lux | Temperatura %.1f C\n", humedad, luz, temperatura);
  enviarLectura(humedad, luz, temperatura);

  unsigned long usado = millis() - inicio;
  if (usado < INTERVALO_MS) delay(INTERVALO_MS - usado);
}
