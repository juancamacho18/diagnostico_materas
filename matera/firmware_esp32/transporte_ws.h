// Canal WebSocket: /ws/dispositivos. El token se presenta una vez por sesión.
#pragma once

#include <WebSocketsClient.h>

WebSocketsClient ws;
bool wsConectado = false;
bool autenticado = false;
unsigned long ultimoIntentoEmparejar = 0;
unsigned long ultimaLectura = 0;

void pedirToken() {
  ws.sendTXT(String("{\"tipo\":\"emparejar\",\"dispositivo\":\"") + dispositivoId + "\"}");
  ultimoIntentoEmparejar = millis();
}

void iniciarSesion() {
  if (token.length() > 0) ws.sendTXT(String("{\"tipo\":\"autenticar\",\"token\":\"") + token + "\"}");
  else pedirToken();
}

void procesarMensaje(const String &mensaje) {
  String tipo = textoJson(mensaje, "tipo");
  if (tipo == "token") {
    guardarToken(textoJson(mensaje, "token"));
    iniciarSesion();
  } else if (tipo == "autenticado") {
    autenticado = true;
    Serial.println("Sesión iniciada por WebSocket.");
  } else if (tipo == "ok") {
    guardarRespuesta(mensaje);
  } else if (tipo == "error") {
    String codigo = textoJson(mensaje, "error");
    Serial.printf("Error del servidor: %s\n", codigo.c_str());
    if (codigo == "TOKEN_INVALIDO") {
      autenticado = false;
      olvidarToken();
      pedirToken();
    } else if (codigo == "EMPAREJAMIENTO_NO_DISPONIBLE") {
      Serial.printf("Esperando emparejamiento: registra %s en el front.\n", dispositivoId.c_str());
    }
  }
}

void eventoWs(WStype_t tipo, uint8_t *datos, size_t largo) {
  if (tipo == WStype_CONNECTED) {
    Serial.println("WebSocket conectado.");
    wsConectado = true;
    autenticado = false;
    iniciarSesion();
  } else if (tipo == WStype_DISCONNECTED) {
    wsConectado = false;
    autenticado = false;
  } else if (tipo == WStype_TEXT) {
    procesarMensaje(String((const char *)datos));
  }
}

bool transporteSesionActiva() { return autenticado; }

void transporteIniciar() {
  ws.begin(SERVIDOR_HOST, SERVIDOR_PUERTO, "/ws/dispositivos");
  ws.onEvent(eventoWs);
  ws.setReconnectInterval(5000);
  ws.enableHeartbeat(15000, 3000, 2);
}

void transporteBucle() {
  ws.loop();
  if (wsConectado && !autenticado && token.length() == 0 && millis() - ultimoIntentoEmparejar > REINTENTO_EMPAREJAR_MS) {
    pedirToken();
  }
  if (autenticado && millis() - ultimaLectura >= INTERVALO_MS) {
    ultimaLectura = millis();
    char cuerpo[224];
    armarLectura(cuerpo, sizeof(cuerpo), "\"tipo\":\"lectura\",");
    ws.sendTXT(cuerpo);
  }
}
