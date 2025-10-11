#include <Wire.h>

//SCD30 I2C communication failure: previous SCD libraries incompatible or may have
// hardware issues need diagnosed. Complete IoT pipeline ready but sensor communication blocked.


void setup() {
  Serial.begin(115200);
  
  // Test with internal pull-ups first
  pinMode(21, INPUT_PULLUP);
  pinMode(22, INPUT_PULLUP);
  Wire.begin(21, 22);
  delay(1000);
  
  Serial.println("=== I2C Emergency Test ===");
  
  // Test if ANY I2C device responds
  byte error, address;
  int found = 0;
  
  for(address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    
    if (error == 0) {
      Serial.print("Found device at 0x");
      Serial.println(address, HEX);
      found++;
    }
  }
  
  if (found == 0) {
    Serial.println("NO I2C DEVICES FOUND - Hardware issue confirmed");
    Serial.println("Check: 3.3V power, pull-up resistors, wiring");
  }
}

void loop() {}