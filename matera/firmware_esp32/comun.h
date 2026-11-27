// Lo que comparten los tres canales: Wi-Fi, reloj, potenciómetros, JSON simple y estado del servidor.
#pragma once

#include <WiFi.h>
#include <Preferences.h>
#include <time.h>

#if USAR_OLED
#include "pantalla.h"
#endif

const int PIN_HUMEDAD = 32;
const int PIN_LUZ = 33;
const int PIN_TEMPERATURA = 34;

const float HUMEDAD_MAX = 100.0;       // %
const float LUZ_MAX = 20000.0;         // lux
const float TEMPERATURA_MAX = 45.0;    // °C
const int MUESTRAS = 16;

const unsigned long ESPERA_WIFI_MS = 15000;
const unsigned long REINTENTO_EMPAREJAR_MS = 5000;
const time_t HORA_MINIMA_VALIDA = 1700000000;

Preferences memoria;
String dispositivoId;
String token;

String estadoPlanta = "";
int puntos = 0;
int variacion = 0;
unsigned long ultimaRespuesta = 0;

bool transporteSesionActiva();

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
    Serial.println("\nSin Wi-Fi. Se reintenta.");
    return false;
  }
  Serial.printf("\nConectado. IP: %s\n", WiFi.localIP().toString().c_str());
  return true;
}

void sincronizarReloj() {
  configTime(0, 0, "pool.ntp.org", "time.google.com");
  unsigned long inicio = millis();
  while (time(nullptr) < HORA_MINIMA_VALIDA && millis() - inicio < ESPERA_WIFI_MS) delay(250);
  Serial.println(time(nullptr) < HORA_MINIMA_VALIDA ? "Reloj sin sincronizar: el servidor pondrá la hora."
                                                    : "Reloj sincronizado.");
}

bool marcaDeTiempo(char *destino, size_t largo) {
  time_t ahora = time(nullptr);
  if (ahora < HORA_MINIMA_VALIDA) return false;
  struct tm fecha;
  gmtime_r(&ahora, &fecha);
  strftime(destino, largo, "%Y-%m-%dT%H:%M:%SZ", &fecha);
  return true;
}

float leerPromedio(int pin) {
  long suma = 0;
  for (int i = 0; i < MUESTRAS; i++) {
    suma += analogRead(pin);
    delay(2);
  }
  return suma / (float)MUESTRAS;
}

float escalar(float crudo, float maximo) {
  return (crudo / 4095.0f) * maximo;
}

// JSON de una lectura. El prefijo va al inicio: "tipo":"lectura", (WebSocket) o "token":"...", (MQTT).
void armarLectura(char *destino, size_t largo, const String &prefijo) {
  float humedad = escalar(leerPromedio(PIN_HUMEDAD), HUMEDAD_MAX);
  float luz = escalar(leerPromedio(PIN_LUZ), LUZ_MAX);
  float temperatura = escalar(leerPromedio(PIN_TEMPERATURA), TEMPERATURA_MAX);
  Serial.printf("Humedad %.1f %% | Luz %.0f lux | Temperatura %.1f C\n", humedad, luz, temperatura);

  char marca[24];
  char campoMarca[48] = "";
  if (marcaDeTiempo(marca, sizeof(marca))) {
    snprintf(campoMarca, sizeof(campoMarca), "\"marcaTiempo\":\"%s\",", marca);
  }
  snprintf(destino, largo,
           "{%s\"dispositivo\":\"%s\",%s\"humedad\":%.1f,\"luz\":%.0f,\"temperatura\":%.1f}",
           prefijo.c_str(), dispositivoId.c_str(), campoMarca, humedad, luz, temperatura);
}

// "clave":"valor" en un JSON plano.
String textoJson(const String &json, const char *clave) {
  String buscada = String("\"") + clave + "\"";
  int desde = 0;
  while (true) {
    int i = json.indexOf(buscada, desde);
    if (i < 0) return "";
    int j = i + buscada.length();
    while (j < (int)json.length() && json[j] == ' ') j++;
    if (j < (int)json.length() && json[j] == ':') {
      j = json.indexOf('"', j);
      if (j < 0) return "";
      int fin = json.indexOf('"', j + 1);
      return fin < 0 ? "" : json.substring(j + 1, fin);
    }
    desde = i + 1;
  }
}

// "clave":numero en un JSON plano.
int numeroJson(const String &json, const char *clave, int defecto) {
  String buscada = String("\"") + clave + "\"";
  int i = json.indexOf(buscada);
  if (i < 0) return defecto;
  int j = json.indexOf(':', i + buscada.length());
  return j < 0 ? defecto : json.substring(j + 1).toInt();
}

void guardarToken(const String &nuevo) {
  token = nuevo;
  memoria.putString("token", token);
  Serial.println("Emparejado: token guardado en la memoria del ESP32.");
}

void olvidarToken() {
  token = "";
  memoria.remove("token");
}

void guardarRespuesta(const String &json) {
  estadoPlanta = textoJson(json, "estado");
  puntos = numeroJson(json, "puntos", puntos);
  variacion = numeroJson(json, "variacion", 0);
  ultimaRespuesta = millis();
  Serial.printf("Servidor: %s | %d puntos (%+d)\n", estadoPlanta.c_str(), puntos, variacion);
}

#if USAR_OLED
Cara caraActual() {
  if (WiFi.status() != WL_CONNECTED) return CARA_SIN_CONEXION;
  if (!transporteSesionActiva() || ultimaRespuesta == 0) return CARA_ESPERANDO;
  if (millis() - ultimaRespuesta > 3 * INTERVALO_MS + 2000) return CARA_SIN_CONEXION;
  if (estadoPlanta == "SALUDABLE") return CARA_FELIZ;
  if (estadoPlanta == "EN_RIESGO") return CARA_PREOCUPADA;
  if (estadoPlanta == "CRITICO") return CARA_TRISTE;
  return CARA_ESPERANDO;
}
#endif

void refrescarPantalla() {
#if USAR_OLED
  static unsigned long ultimoDibujo = 0;
  if (millis() - ultimoDibujo < 100) return;
  ultimoDibujo = millis();
  bool parpadeo = millis() % 4000 < 180;
  pantallaMostrar(caraActual(), puntos, variacion, parpadeo);
#endif
}
