#include <Arduino.h>
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#include "SparkFun_SCD30_Arduino_Library.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// WiFi Configuration
const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://192.168.1.100:8000/readings";

unsigned long lastUploadTime = 0;
const unsigned long uploadInterval = 10000;

// Sensor and Display
SCD30 airSensor;
Adafruit_SH1107 display = Adafruit_SH1107(64, 128, &Wire);

// Pin definitions
const unsigned int buttonPin = 27;
const unsigned int redLed = 33;
const unsigned int greenLed = 15;
const unsigned int blueLed = 32;
const unsigned int piezo = 14;
const unsigned int tripLevel = 5000;

bool alm_1 = false;
bool alm_2 = false;
bool alertDisp = false;

void IRAM_ATTR isr_clearAlarm() {
  alm_2 = false;
}

void connectToWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(" Connected!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println(" Failed!");
  }
}

void uploadToAPI(int co2, float temp, float humidity) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected, skipping upload");
    return;
  }
  
  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<200> doc;
  doc["sensor_id"] = "ESP32_CO2_SYSTEM";
  doc["co2_ppm"] = co2;
  doc["temperature"] = temp;
  doc["humidity"] = humidity;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.print("Uploading: ");
  Serial.println(jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("Upload successful!");
  } else {
    Serial.print("Upload failed! Error: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
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
  delay(1000);
  
  Serial.println("=== CO2 Monitoring System Starting ===");
  
  // I2C Scanner to detect devices
  Serial.println("Scanning I2C devices...");
  Wire.begin(23, 22); // FEATHER I2C PINS: SDA=23, SCL=22
  delay(1000);
  
  bool foundOLED = false;
  bool foundSCD30 = false;
  
  for(int addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    byte error = Wire.endTransmission();
    
    if(error == 0) {
      Serial.print("FOUND: 0x");
      Serial.println(addr, HEX);
      
      if(addr == 0x3C) {
        Serial.println("  ^ OLED Display");
        foundOLED = true;
      }
      if(addr == 0x61) {
        Serial.println("  ^ SCD30 Sensor");
        foundSCD30 = true;
      }
    }
  }
  
  if(!foundOLED || !foundSCD30) {
    Serial.println("ERROR: Missing required I2C devices!");
    if(!foundOLED) Serial.println("  - OLED not found at 0x3C");
    if(!foundSCD30) Serial.println("  - SCD30 not found at 0x61");
    while(1); // Halt if devices missing
  }
  
  Serial.println("All I2C devices detected successfully!");
  
  // Initialize OLED Display
  display.begin(0x3C, true);
  display.setRotation(1);
  display.setTextSize(2);
  display.setTextColor(SH110X_WHITE);
  display.setCursor(0,0);
  display.println("System");
  display.println(" Starting");
  display.display();
  delay(2000);
  display.clearDisplay();
  
  // Initialize pins
  pinMode(buttonPin, INPUT);
  pinMode(blueLed, OUTPUT);
  pinMode(redLed, OUTPUT);
  pinMode(greenLed, OUTPUT);
  pinMode(piezo, OUTPUT);
  
  digitalWrite(blueLed, LOW);
  digitalWrite(redLed, LOW);
  digitalWrite(greenLed, LOW);
  digitalWrite(piezo, LOW);
  
  // Initialize SCD30 Sensor
  Serial.println("Initializing SCD30...");
  display.setCursor(0,0);
  display.clearDisplay();
  display.println("Init");
  display.println("Sensor");
  display.display();
  
  if (!airSensor.begin()) {
    Serial.println("SCD30 initialization failed!");
    display.clearDisplay();
    display.println(" SENSOR");
    display.println("  ERROR");
    display.display();
    while(1);
  }
  
  Serial.println("SCD30 initialized successfully!");
  
  // Connect to WiFi
  display.clearDisplay();
  display.println("WiFi");
  display.println("Connect...");
  display.display();
  connectToWiFi();
  
  // System ready
  display.clearDisplay();
  display.println(" System");
  display.println("  Ready");
  display.display();
  delay(1000);
  display.clearDisplay();
  
  attachInterrupt(buttonPin, isr_clearAlarm, RISING);
  
  Serial.println("=== System Ready ===");
}

void loop() {
  if (airSensor.dataAvailable()) {  
    digitalWrite(blueLed, HIGH);
    display.setCursor(0,0);
    display.clearDisplay();
    
    int co2 = airSensor.getCO2();
    float temperature = airSensor.getTemperature();
    float humidity = airSensor.getHumidity();
    
    // Upload to API every 10 seconds
    unsigned long currentTime = millis();
    if (WiFi.status() == WL_CONNECTED && currentTime - lastUploadTime >= uploadInterval) {
      uploadToAPI(co2, temperature, humidity);
      lastUploadTime = currentTime;
    }
    
    alertDisp = evaluate(co2 > tripLevel);
    
    // Display on OLED
    display.println("    CO2");
    display.print("  ");
    display.print(co2);
    display.println(" PPM");
    display.print("T:");
    display.print(temperature, 1);
    display.print("C H:");
    display.print(humidity, 0);
    display.println("%");
    
    // Show WiFi status
    if (WiFi.status() == WL_CONNECTED) {
      display.println("WiFi: OK");
    } else {
      display.println("WiFi: OFF");
    }
 
    if (alertDisp) {
      display.println(" ALERT !!!");
    }
    
    // Serial output
    Serial.print("CO2: ");
    Serial.print(co2);
    Serial.print(" ppm, Temp: ");
    Serial.print(temperature, 1);
    Serial.print("C, Humidity: ");
    Serial.print(humidity, 0);
    Serial.println("%");
    
    updateLeds();
  } else {  
    digitalWrite(blueLed, LOW);
    Serial.println("Waiting for sensor data...");
  }

  display.display();
  delay(1000);
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