#include <Arduino.h>
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#include "SparkFun_SCD30_Arduino_Library.h"

SCD30 airSensor;
Adafruit_SH1107 display = Adafruit_SH1107(64, 128, &Wire);

const unsigned int buttonPin = 27;
const unsigned int redLed = 33;
const unsigned int greenLed = 15;
const unsigned int blueLed = 32;
const unsigned int piezo = 14;
const unsigned int tripLevel = 1000;

bool alm_1 = false;
bool alm_2 = false;
bool alertDisp = false;

void IRAM_ATTR isr_clearAlarm() {
  alm_2 = false;
}

void alert() { 
    for (int i = 0; i <= 255; i++) {
        if (!alm_2) {break;}
        analogWrite(piezo, i);
        analogWrite(redLed, i);
        delay(5);
    }    
    digitalWrite(blueLed, LOW);
    for (int i = 255; i >= 0; i--) {
        if (!alm_2) {break;}
        analogWrite(piezo, i);
        analogWrite(redLed, i);
        delay(5);
    }
}

void setup() {
  Serial.begin(115200);
  
  // Initialize I2C with the correct Feather pins
  Wire.begin(23, 22); // SDA=23, SCL=22 for ESP32 Feather
  delay(1000); // Let I2C stabilize
  
  display.begin(0x3C, true);
  display.setRotation(1);
  display.setTextSize(2);
  display.setTextColor(SH110X_WHITE);
  display.setCursor(0,0);
  display.display();
  delay(500);
  display.clearDisplay();
  
  // Only set up pins we actually use
  pinMode(buttonPin, INPUT);
  pinMode(blueLed, OUTPUT);
  pinMode(redLed, OUTPUT);
  pinMode(greenLed, OUTPUT);
  pinMode(piezo, OUTPUT);
  
  digitalWrite(blueLed, LOW);
  digitalWrite(redLed, LOW);
  digitalWrite(greenLed, LOW);
  digitalWrite(piezo, LOW);
  
  Serial.println("Starting SCD30 initialization...");

  // Try SCD30 initialization with timeout
  unsigned long startTime = millis();
  bool sensorInitialized = false;
  
  while (millis() - startTime < 10000) { // 10 second timeout
    if (airSensor.begin()) {
      sensorInitialized = true;
      break;
    }
    delay(500);
    Serial.print(".");
  }
  
  if (!sensorInitialized) {
    Serial.println("\nSCD30 INIT FAILED - Check hardware connections");
    digitalWrite(blueLed, LOW);
    display.setCursor(0,0);
    display.clearDisplay();
    display.println(" SENSOR");
    display.println("  ERROR");
    display.display();
    
    while(1); // Halt
  }
  
  Serial.println("\nSCD30 initialized successfully!");
  display.clearDisplay();
  display.display();
  attachInterrupt(buttonPin, isr_clearAlarm, RISING);
}

void loop() {
  if (airSensor.dataAvailable()) {  
    digitalWrite(blueLed, HIGH);
    display.setCursor(0,0);
    display.clearDisplay();
    
    int value = airSensor.getCO2();
    alertDisp = evaluate(value > tripLevel);
    
    display.print("");
    display.println("     CO2");
    display.print("  ");
    display.print(value);
    display.println(" PPM");  
 
    if (alertDisp) {
      display.println(" ALERT !!!");
    }  
    updateLeds();
    
    // Also print to Serial for debugging
    Serial.print("CO2: ");
    Serial.print(value);
    Serial.println(" PPM");
  } else {  
    digitalWrite(blueLed, LOW);
    Serial.println("No sensor data available");
  }

  yield();
  display.display();
  delay(1000); // Add small delay to prevent flooding
}

bool evaluate(bool tripState) {
  if (tripState) {
    if (!alm_1) {
      alm_1 = true;
      alm_2 = true;
    }
  } else {
    alm_1 = false;
    alm_2 = false;
  }
  return tripState;
}

void updateLeds() {
  if (alm_1 && alm_2) {
    digitalWrite(greenLed, LOW);
    alert();
  } else if (!alm_1 && !alm_2) {
    digitalWrite(greenLed, HIGH);
    analogWrite(redLed, 0);
    digitalWrite(piezo, LOW);
  } else if (alm_1 && !alm_2) {
    digitalWrite(greenLed, LOW);
    digitalWrite(redLed, HIGH);
    analogWrite(piezo, LOW);
  }
}