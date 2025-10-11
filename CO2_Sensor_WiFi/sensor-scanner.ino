#include <Wire.h>

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // USE FEATHER I2C PINS
  Wire.begin(23, 22); // SDA=23, SCL=22 for ESP32 Feather
  delay(1000);
  
  Serial.println("=== FEATHER I2C SCAN ===");
  Serial.println("Using SDA=23, SCL=22");
  
  bool found = false;
  for(int addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    byte error = Wire.endTransmission();
    
    if(error == 0) {
      Serial.print("FOUND: 0x");
      Serial.println(addr, HEX);
      
      if(addr == 0x3C) Serial.println("  ^ This is the OLED display!");
      if(addr == 0x61) Serial.println("  ^ This is the SCD30 sensor!");
      found = true;
    }
  }
  
  if(!found) {
    Serial.println("NO I2C DEVICES - Check Feather wiring");
  } else {
    Serial.println("I2C scan complete - devices found!");
  }
}

void loop() {}