// Canal HTTP: POST /api/dispositivos/{id}/emparejar y /lecturas con el token en la cabecera Authorization.
#pragma once

#include <HTTPClient.h>

const int TIEMPO_LIMITE_HTTP_MS = 5000;
unsigned long ultimaLectura = 0;
unsigned long ultimoIntentoEmparejar = 0;

String urlBase() { return String("http://") + SERVIDOR_HOST + ":" + SERVIDOR_PUERTO; }

void emparejar() {
  ultimoIntentoEmparejar = millis();
  HTTPClient http;
  http.setTimeout(TIEMPO_LIMITE_HTTP_MS);
  http.begin(urlBase() + "/api/dispositivos/" + dispositivoId + "/emparejar");
  int codigo = http.POST("");
  String respuesta = codigo > 0 ? http.getString() : "";
  http.end();
  if (codigo == 200) guardarToken(textoJson(respuesta, "token"));
  else Serial.printf("Esperando emparejamiento (%d): registra %s en el front.\n", codigo, dispositivoId.c_str());
}

void enviarLectura() {
  char cuerpo[224];
  armarLectura(cuerpo, sizeof(cuerpo), "");
  HTTPClient http;
  http.setTimeout(TIEMPO_LIMITE_HTTP_MS);
  http.begin(urlBase() + "/api/dispositivos/" + dispositivoId + "/lecturas");
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", String("Bearer ") + token);
  int codigo = http.POST(cuerpo);
  if (codigo > 0) {
    String respuesta = http.getString();
    Serial.printf("POST -> %d %s\n", codigo, respuesta.c_str());
    if (codigo == 201) guardarRespuesta(respuesta);
    if (codigo == 401) olvidarToken();
  } else {
    Serial.printf("No se pudo enviar: %s\n", http.errorToString(codigo).c_str());
  }
  http.end();
}

bool transporteSesionActiva() { return token.length() > 0; }

void transporteIniciar() {}

void transporteBucle() {
  if (token.length() == 0) {
    if (millis() - ultimoIntentoEmparejar > REINTENTO_EMPAREJAR_MS || ultimoIntentoEmparejar == 0) emparejar();
    return;
  }
  if (millis() - ultimaLectura >= INTERVALO_MS || ultimaLectura == 0) {
    ultimaLectura = millis();
    enviarLectura();
  }
}
