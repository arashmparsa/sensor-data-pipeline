#include <Arduino.h>
#include <analogWrite.h>
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#include "SparkFun_SCD30_Arduino_Library.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>  // Install via Library Manager

// ==================== WiFi Configuration ====================
const char* ssid = "";           // Your WiFi name
const char* password = "!!";   // Your WiFi password
const char* serverUrl = ":8000/readings";  // Your laptop's IP #https the ipconfig in the commend prompt for ipv4

// For local testing: "http://192.168.1.100:8000/readings"
// For cloud: "http://your-server.com/readings"

unsigned long lastUploadTime = 0;
const unsigned long uploadInterval = 10000;  // Upload every 10 seconds

// ==================== Existing Hardware Setup ====================
SCD30 airSensor;
Adafruit_SH110X display = Adafruit_SH110X(64, 128, &Wire);

const int buttonPin = A10;
int safe = 12;
int led = 25;
int led2 = 34;
int a = 26;
int i = 0;

int buttonState = LOW;
int buttonPushCounter = 0;
bool SilenceAlarm = true;

// ==================== WiFi Functions ====================
void connectWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    
    // Show on OLED
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("WiFi OK");
    display.print("IP:");
    display.println(WiFi.localIP());
    display.display();
    delay(2000);
  } else {
    Serial.println("\nWiFi Connection Failed!");
    digitalWrite(led2, HIGH);  // Show error on LED
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
  
  // Create JSON payload
  StaticJsonDocument<200> doc;
  doc["sensor_id"] = "ESP32_SENSOR_001";  // Unique ID for your device
  doc["co2_ppm"] = co2;
  doc["temperature"] = temp;
  doc["humidity"] = humidity;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.print("Uploading: ");
  Serial.println(jsonString);
  
  // Send POST request
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.print("Upload successful! Response: ");
    Serial.println(response);
    
    // Brief flash to show upload success
    digitalWrite(safe, HIGH);
    delay(50);
    digitalWrite(safe, LOW);
  } else {
    Serial.print("Upload failed! Error: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
}

// ==================== Setup ====================
void setup() {
  Serial.begin(115200);
  
  // Initialize display
  display.begin(0x3C, true);
  display.setRotation(1);
  display.setTextSize(2);
  display.setTextColor(SH110X_WHITE);
  display.setCursor(0, 0);
  display.display();
  delay(500);
  display.clearDisplay();
  
  // Setup pins
  digitalWrite(safe, LOW);
  pinMode(buttonPin, INPUT);
  pinMode(25, OUTPUT);
  pinMode(26, OUTPUT);
  pinMode(34, OUTPUT);
  
  // Initialize I2C
  Wire.begin();
  
  // Check CO2 sensor
  if (airSensor.begin() == false) {
    digitalWrite(led2, HIGH);
    Serial.println("Air sensor not detected!");
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("SENSOR");
    display.println("ERROR!");
    display.display();
    while (1);
  }
  
  // Connect to WiFi
  connectWiFi();
  
  Serial.println("System Ready!");
}

// ==================== Main Loop ====================
void loop() {
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, reconnecting...");
    connectWiFi();
  }
  
  // Check button press
  if (digitalRead(buttonPin) == HIGH) {
    buttonPushCounter++;
    Serial.println("Button pressed");
  } else {
    buttonPushCounter = 0;
  }
  
  // Read sensor data
  if (airSensor.dataAvailable()) {
    display.setCursor(0, 0);
    display.clearDisplay();
    
    int co2Value = airSensor.getCO2();
    float temperature = airSensor.getTemperature();
    float humidity = airSensor.getHumidity();
    
    // Display on OLED
    display.println("  CO2");
    display.print(" ");
    display.print(co2Value);
    display.println(" PPM");
    display.print("T:");
    display.print(temperature, 1);
    display.print("C ");
    display.print("H:");
    display.print(humidity, 0);
    display.println("%");
    
    // Show WiFi status
    if (WiFi.status() == WL_CONNECTED) {
      display.println("WiFi OK");
    } else {
      display.println("WiFi ERR");
    }
    
    // Upload to API every 10 seconds
    unsigned long currentTime = millis();
    if (currentTime - lastUploadTime >= uploadInterval) {
      uploadToAPI(co2Value, temperature, humidity);
      lastUploadTime = currentTime;
    }
    
    // Sound alarm if threshold exceeded
    if (co2Value > 700) {
      alert();
    } else if (co2Value <= 700) {
      SilenceAlarm = false;
      analogWrite(safe, HIGH);
    }
  }
  
  yield();
  display.display();
}

// ==================== Alert Functions ====================
void alert() {
  for (int i = 0; i <= 255; i++) {
    SoundAlarm(i);
    if (buttonPushCounter != 0) {
      SilenceAlarm = true;
    }
    delay(5);
  }
  for (int i = 255; i >= 0; i--) {
    SoundAlarm(i);
    if (buttonPushCounter != 0) {
      SilenceAlarm = true;
    }
    delay(5);
  }
}

void SoundAlarm(int i) {
  if (SilenceAlarm) {
    analogWrite(safe, HIGH);
    analogWrite(a, LOW);
    analogWrite(led, LOW);
  } else {
    analogWrite(safe, LOW);
    analogWrite(a, i);
    analogWrite(led, i);
  }
}