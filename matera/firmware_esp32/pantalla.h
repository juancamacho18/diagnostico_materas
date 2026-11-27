// Pantalla OLED SSD1306 de 128x64 por I2C: una carita segun el estado
// que diagnostica el servidor y los puntos de la planta.
// Libreria: "Adafruit SSD1306" (instala tambien "Adafruit GFX").
//
//   OLED VCC -> 3V3     OLED GND -> GND
//   OLED SDA -> GPIO21  OLED SCL -> GPIO22

#pragma once

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <math.h>
#include <stdio.h>

const int PIN_OLED_SDA = 21;
const int PIN_OLED_SCL = 22;
const int OLED_ANCHO = 128;
const int OLED_ALTO = 64;
const uint8_t OLED_DIRECCION = 0x3C;  // algunas pantallas usan 0x3D

enum Cara { CARA_SIN_CONEXION, CARA_ESPERANDO, CARA_FELIZ, CARA_PREOCUPADA, CARA_TRISTE };

const int CARA_X = 32;  // centro de la carita
const int CARA_Y = 32;

Adafruit_SSD1306 oled(OLED_ANCHO, OLED_ALTO, &Wire, -1);
bool oledListo = false;

// Arco de circunferencia (grados; 0 = derecha, 90 = abajo) con trazo de 2 px.
void dibujarArco(Adafruit_GFX &d, int cx, int cy, int radio, int desde, int hasta) {
  for (int grosor = 0; grosor < 2; grosor++) {
    float anteriorX = 0, anteriorY = 0;
    for (int grados = desde; grados <= hasta; grados += 5) {
      float radianes = grados * 3.14159265f / 180.0f;
      float x = cx + (radio - grosor) * cosf(radianes);
      float y = cy + (radio - grosor) * sinf(radianes);
      if (grados > desde) d.drawLine((int)anteriorX, (int)anteriorY, (int)x, (int)y, SSD1306_WHITE);
      anteriorX = x;
      anteriorY = y;
    }
  }
}

void dibujarOjos(Adafruit_GFX &d, bool cerrados) {
  for (int lado = -1; lado <= 1; lado += 2) {
    int x = CARA_X + lado * 11;
    if (cerrados) d.drawLine(x - 4, CARA_Y - 8, x + 4, CARA_Y - 8, SSD1306_WHITE);
    else d.fillCircle(x, CARA_Y - 8, 3, SSD1306_WHITE);
  }
}

void dibujarCara(Adafruit_GFX &d, Cara cara, bool parpadeo) {
  d.drawCircle(CARA_X, CARA_Y, 30, SSD1306_WHITE);

  switch (cara) {
    case CARA_FELIZ:
      dibujarOjos(d, parpadeo);
      dibujarArco(d, CARA_X, CARA_Y + 2, 14, 20, 160);
      break;

    case CARA_PREOCUPADA:
      dibujarOjos(d, parpadeo);
      d.drawLine(CARA_X - 17, CARA_Y - 14, CARA_X - 7, CARA_Y - 19, SSD1306_WHITE);
      d.drawLine(CARA_X + 7, CARA_Y - 19, CARA_X + 17, CARA_Y - 14, SSD1306_WHITE);
      d.drawLine(CARA_X - 8, CARA_Y + 12, CARA_X + 8, CARA_Y + 12, SSD1306_WHITE);
      d.drawLine(CARA_X - 8, CARA_Y + 13, CARA_X + 8, CARA_Y + 13, SSD1306_WHITE);
      break;

    case CARA_TRISTE:
      dibujarOjos(d, parpadeo);
      dibujarArco(d, CARA_X, CARA_Y + 22, 12, 205, 335);
      d.fillCircle(CARA_X + 17, CARA_Y + 1, 2, SSD1306_WHITE);  // lagrima
      break;

    case CARA_ESPERANDO:
      d.drawCircle(CARA_X - 11, CARA_Y - 8, 4, SSD1306_WHITE);
      d.drawCircle(CARA_X + 11, CARA_Y - 8, 4, SSD1306_WHITE);
      d.drawCircle(CARA_X, CARA_Y + 12, 4, SSD1306_WHITE);
      break;

    case CARA_SIN_CONEXION:
      dibujarOjos(d, true);
      d.drawLine(CARA_X - 5, CARA_Y + 12, CARA_X + 5, CARA_Y + 12, SSD1306_WHITE);
      d.setTextSize(1);
      d.setTextColor(SSD1306_WHITE);
      d.setCursor(CARA_X + 20, CARA_Y - 26);
      d.print("z");
      break;
  }
}

const char *etiquetaDeCara(Cara cara) {
  switch (cara) {
    case CARA_FELIZ: return "BIEN";
    case CARA_PREOCUPADA: return "RIESGO";
    case CARA_TRISTE: return "CRITICO";
    case CARA_ESPERANDO: return "ESPERA";
    default: return "SIN RED";
  }
}

void dibujarMarcador(Adafruit_GFX &d, Cara cara, int puntos, int variacion) {
  char texto[12];
  d.setTextColor(SSD1306_WHITE);

  d.setTextSize(1);
  d.setCursor(72, 2);
  d.print("PUNTOS");

  snprintf(texto, sizeof(texto), "%d", puntos);
  d.setTextSize(puntos >= 1000 ? 2 : 3);
  d.setCursor(72, 14);
  d.print(texto);

  if (variacion != 0) {
    snprintf(texto, sizeof(texto), "%+d", variacion);
    d.setTextSize(2);
    d.setCursor(72, 38);
    d.print(texto);
  }

  d.setTextSize(1);
  d.setCursor(72, 56);
  d.print(etiquetaDeCara(cara));
}

void pantallaIniciar() {
  Wire.begin(PIN_OLED_SDA, PIN_OLED_SCL);
  oledListo = oled.begin(SSD1306_SWITCHCAPVCC, OLED_DIRECCION);
  if (!oledListo) return;
  oled.clearDisplay();
  oled.display();
}

void pantallaMostrar(Cara cara, int puntos, int variacion, bool parpadeo) {
  if (!oledListo) return;
  oled.clearDisplay();
  dibujarCara(oled, cara, parpadeo);
  dibujarMarcador(oled, cara, puntos, variacion);
  oled.display();
}
