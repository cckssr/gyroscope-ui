// gyroscope.cpp
// Hauptmodul für Gyroskop-Messung und WiFi-Server
// Board: Arduino Nano ESP32
// Sensor: LSM6DS3
// Version: 0.9

#include <WiFi.h>
#include "secrets.h"
#include <Arduino_LSM6DS3.h>
#include <Arduino.h>
#include <SPI.h>

#define LSM_CS 7
#define LSM_SCK 13
#define LSM_MISO 12
#define LSM_MOSI 11
#define SOFTWARE_VERSION "0.9"
#define OPENBIS_CODE "E95454"
#define PORT 80
#define IP_ADDRESS "192.168.4.1"

WiFiServer server(PORT);

// Debugging aktivieren/deaktivieren
bool DEBUG_MODE = true;

// Sensorwerte
struct SensorData
{
  float accelX, accelY, accelZ;
  float gyroX, gyroY, gyroZ;
};

void setupWiFi()
{
  Serial.println("Starte WiFi...");
  WiFi.mode(WIFI_AP);
  WiFi.softAP(SECRET_SSID, SECRET_PASS);
  Serial.print("Access Point IP: ");
  Serial.println(WiFi.softAPIP());
  server.begin();
}

void setupSensor()
{
  if (!IMU.begin())
  {
    Serial.println("LSM6DS3 nicht gefunden!");
    while (1)
    {
      delay(1000);
    }
  }
  Serial.println("LSM6DS3 erkannt!");
}

SensorData readSensor()
{
  SensorData data;
  IMU.readAcceleration(data.accelX, data.accelY, data.accelZ);
  IMU.readGyroscope(data.gyroX, data.gyroY, data.gyroZ);
  return data;
}

void debugPrint(const SensorData &data)
{
  Serial.print("ACCEL: ");
  Serial.print(data.accelX);
  Serial.print(", ");
  Serial.print(data.accelY);
  Serial.print(", ");
  Serial.print(data.accelZ);
  Serial.print(" | GYRO: ");
  Serial.print(data.gyroX);
  Serial.print(", ");
  Serial.print(data.gyroY);
  Serial.print(", ");
  Serial.println(data.gyroZ);
}

// Minimaler Test für LSM6DS3 auf Arduino Nano ESP32
#include <Arduino.h>
#include <Arduino_LSM6DS3.h>

void setup() {
  Serial.begin(115200);
  while (!Serial) {}
  if (!IMU.begin()) {
    Serial.println("LSM6DS3 nicht gefunden!");
    while (1) {
      delay(1000);
    }
  }
  Serial.println("LSM6DS3 erkannt!");
}

void loop() {
  float ax, ay, az;
  float gx, gy, gz;
  if (IMU.readAcceleration(ax, ay, az) && IMU.readGyroscope(gx, gy, gz)) {
    Serial.print("ACCEL: ");
    Serial.print(ax); Serial.print(", ");
    Serial.print(ay); Serial.print(", ");
    Serial.print(az);
    Serial.print(" | GYRO: ");
    Serial.print(gx); Serial.print(", ");
    Serial.print(gy); Serial.print(", ");
    Serial.println(gz);
  } else {
    Serial.println("Sensorwerte konnten nicht gelesen werden.");
  }
  delay(500);
}

// ...nur die minimalistische Testversion bleibt erhalten...
