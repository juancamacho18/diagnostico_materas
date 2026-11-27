// Canal MQTT: temas matera/{id}/emparejar, /lectura y /respuesta. El token viaja en la carga, nunca en el tema.
#pragma once

#include <PubSubClient.h>

#ifndef MQTT_HOST
#define MQTT_HOST SERVIDOR_HOST
#endif
#ifndef MQTT_PUERTO
#define MQTT_PUERTO 1883
#endif

const unsigned long REINTENTO_BROKER_MS = 5000;

WiFiClient redMqtt;
PubSubClient mqtt(redMqtt);
String temaBase;
String temaRespuesta;
unsigned long ultimoIntentoBroker = 0;
unsigned long ultimoIntentoEmparejar = 0;
unsigned long ultimaLectura = 0;

void pedirToken() {
  mqtt.publish((temaBase + "/emparejar").c_str(), "{}");
  ultimoIntentoEmparejar = millis();
}

void alRecibir(char *tema, byte *datos, unsigned int largo) {
  String mensaje;
  mensaje.reserve(largo);
  for (unsigned int i = 0; i < largo; i++) mensaje += (char)datos[i];

  String tipo = textoJson(mensaje, "tipo");
  if (tipo == "token") {
    guardarToken(textoJson(mensaje, "token"));
  } else if (tipo == "ok") {
    guardarRespuesta(mensaje);
  } else if (tipo == "error") {
    String codigo = textoJson(mensaje, "error");
    Serial.printf("Error del servidor: %s\n", codigo.c_str());
    if (codigo == "TOKEN_INVALIDO") {
      olvidarToken();
      pedirToken();
    } else if (codigo == "EMPAREJAMIENTO_NO_DISPONIBLE") {
      Serial.printf("Esperando emparejamiento: registra %s en el front.\n", dispositivoId.c_str());
    }
  }
}

// Se suscribe a su tema de respuesta antes de publicar: ahí llega el token.
bool conectarBroker() {
  if (mqtt.connected()) return true;
  if (millis() - ultimoIntentoBroker < REINTENTO_BROKER_MS) return false;
  ultimoIntentoBroker = millis();
  Serial.printf("Conectando al broker %s:%d\n", MQTT_HOST, MQTT_PUERTO);
  bool listo = (MQTT_USUARIO[0] != '\0') ? mqtt.connect(dispositivoId.c_str(), MQTT_USUARIO, MQTT_CLAVE)
                                         : mqtt.connect(dispositivoId.c_str());
  if (!listo) {
    Serial.printf("Sin broker (estado %d). Se reintenta.\n", mqtt.state());
    return false;
  }
  mqtt.subscribe(temaRespuesta.c_str());
  Serial.println("Broker conectado.");
  return true;
}

bool transporteSesionActiva() { return token.length() > 0 && mqtt.connected(); }

void transporteIniciar() {
  temaBase = String("matera/") + dispositivoId;
  temaRespuesta = temaBase + "/respuesta";
  mqtt.setServer(MQTT_HOST, MQTT_PUERTO);
  mqtt.setCallback(alRecibir);
  mqtt.setBufferSize(768);
  mqtt.setKeepAlive(30);
}

void transporteBucle() {
  if (!conectarBroker()) return;
  mqtt.loop();
  if (token.length() == 0 && millis() - ultimoIntentoEmparejar > REINTENTO_EMPAREJAR_MS) pedirToken();
  if (token.length() > 0 && millis() - ultimaLectura >= INTERVALO_MS) {
    ultimaLectura = millis();
    char cuerpo[512];
    armarLectura(cuerpo, sizeof(cuerpo), String("\"token\":\"") + token + "\",");
    mqtt.publish((temaBase + "/lectura").c_str(), cuerpo);
  }
}
