#include <TFT_eSPI.h>

TFT_eSPI tft = TFT_eSPI();

void setup() {
  // Turn on backlight
  //pinMode(TFT_BL, OUTPUT);
  //digitalWrite(TFT_BL, HIGH);

  tft.init();
  tft.setRotation(0);
  tft.fillScreen(TFT_CYAN);

  // Draw a simple test pattern
  tft.fillCircle(120, 120, 100, TFT_BLUE);
  tft.fillCircle(120, 120, 60, TFT_GREEN);
  tft.fillCircle(120, 120, 20, TFT_RED);

  //tft.setTextColor(TFT_WHITE, TFT_BLUE);
  tft.setTextColor(TFT_BLACK);
  //tft.setFreeFont(TFT_F);
  tft.setTextSize(2);
  tft.setTextDatum(MC_DATUM);
  tft.drawString("Hello!", 120, 120);
}

void loop() {
}