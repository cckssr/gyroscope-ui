/**
 * @file main.cpp
 * @brief Gyroscope Data Acquisition System für Arduino Nano ESP32
 *
 * Dieses Programm implementiert ein Datenerfassungssystem für Gyroscop-Messungen
 * mit folgenden Funktionen:
 * - Auslesen des LSM6DS3-Sensors (Beschleunigung und Winkelgeschwindigkeit)
 * - Hall-Sensor für Frequenzmessung
 * - WiFi-Access Point für direkte Verbindung oder Station-Modus
 * - UDP-Broadcast für effiziente Sensordatenübertragung (Standard)
 * - TCP für HTTP-API und Legacy-Unterstützung
 * - Debug-Modus über serielle Verbindung
 * - HTTP-API für Geräteinformationen und Status
 *
 * Übertragungsmodi:
 * - UDP: Broadcast-basierte Sensordatenübertragung (niedrige Latenz, hoher Durchsatz)
 * - TCP: Verbindungsbasierte Übertragung (zuverlässig, höhere Latenz)
 *
 * WiFi-Modi:
 * - Access Point: Erstellt eigenes WiFi-Netzwerk (Standard)
 * - Station: Verbindet zu bestehendem WiFi-Netzwerk
 *
 * HTTP-API Endpunkte (TCP):
 * - GET /version     - Software-Version abrufen
 * - GET /device-id   - OpenBIS-Code/Geräte-ID abrufen
 * - GET /info        - Vollständige Geräteinformationen
 * - GET /status      - Aktueller System-Status
 *
 * Sensordaten-Empfang:
 * - UDP: nc -u <IP> 12345 (oder socat udp-recv:12345)
 * - TCP: nc <IP> 80
 *
 * @author M. Metschl, C. Kessler
 * @version 1.0.1
 * @date 2025-10-02
 */

#include <Arduino.h>
#include <Adafruit_LSM6DS33.h>
#include <SPI.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include "secrets.h"

// ================================
// SYSTEM CONFIGURATION
// ================================

/** @brief Gerätekennzeichnung für Identifikation */
const char *DEVICE_ID = "E76347";

/** @brief Software-Versionsnummer */
const char *SOFTWARE_VERSION = "1.0.1";

// ================================
// HARDWARE PIN DEFINITIONS
// ================================

/** @brief SPI Chip Select Pin (CS) für LSM6DS3 */
#define LSM_CS 5
/** @brief SPI Clock Pin (SCK) */
#define LSM_SCK 3
/** @brief SPI Master In Slave Out (SA0) Pin */
#define LSM_MISO 4
/** @brief SPI Master Out Slave In (MOSI, SDA) Pin */
#define LSM_MOSI 6

/** @brief Digital Pin für Hall-Sensor */
const int HALL_DIGITAL_PIN = 2;

// ================================
// NETWORK CONFIGURATION
// ================================

/** @brief WiFi-Access Point SSID */
char WIFI_AP_SSID[32]; // Buffer für dynamische SSID

/** @brief WiFi-Access Point Passwort */
const char *WIFI_AP_PASSWORD = SECRET_PASS;
/** @brief Access Point IP-Adresse */
const IPAddress AP_IP(192, 168, 4, 1);
/** @brief Access Point Gateway */
const IPAddress AP_GATEWAY(192, 168, 4, 1);
/** @brief Access Point Subnet-Maske */
const IPAddress AP_SUBNET(255, 255, 255, 0);
/** @brief Server-Port für HTTP-API */
const int HTTP_SERVER_PORT = 80;

/** @brief UDP-Port für kontinuierliche Sensordaten */
const int UDP_PORT = 12345;

/** @brief Broadcast-IP für UDP-Übertragung */
const IPAddress UDP_BROADCAST_IP(192, 168, 4, 255);

/** @brief WiFi-Modus Flag: true = Access Point, false = Station Mode */
const bool WIFI_AP_MODE = true;

/** @brief Datenübertragungsmodus: true = UDP, false = TCP */
const bool USE_UDP_FOR_DATA = true;

/** @brief UDP-Übertragungsmodus: true = Broadcast, false = Unicast zu verbundenen Clients */
const bool USE_UDP_BROADCAST = false;

// ================================
// GLOBAL OBJECTS AND VARIABLES
// ================================

/** @brief WiFi-Server für HTTP-API */
WiFiServer wifiServer(HTTP_SERVER_PORT);

/** @brief UDP-Socket für Sensordatenübertragung */
WiFiUDP udpSocket;

/** @brief Liste der UDP-Client-IPs für Unicast */
IPAddress udpClientIPs[5]; // Maximal 5 UDP-Clients
int udpClientCount = 0;

/** @brief Aktuelle persistente WiFi-Client-Verbindung für kontinuierliche TCP-Daten */
WiFiClient persistentClient;

/** @brief Debug-Modus Flag (aktiviert durch serielle Verbindung) */
bool isDebugMode = false;

/** @brief LSM6DS3 Sensor Objekt */
Adafruit_LSM6DS33 lsm6ds33;

// ================================
// INTERRUPT HANDLING VARIABLES
// ================================

/** @brief Letzter Zeitstempel des Hall-Sensor Interrupts (Mikrosekunden) */
volatile uint32_t lastInterruptTimeUs = 0;

/** @brief Periode zwischen Hall-Sensor Interrupts (Mikrosekunden) */
volatile uint32_t interruptPeriodUs = 0;

/** @brief Mindest-Totzeit zwischen Interrupts (Mikrosekunden) */
volatile uint32_t interruptDeadtimeUs = 1500;

/** @brief Thread-sichere Queue für Interrupt-Daten */
QueueHandle_t interruptQueue;

/** @brief Aktuelle berechnete Frequenz (Hz) */
float currentFrequency = 0.0f;

// ================================
// FREQUENCY CHANGE RATE DETECTION
// ================================

/** @brief Zeit in Millisekunden, nach der bei konstanter Frequenz auf 0 gesetzt wird */
const uint32_t FREQUENCY_STABLE_TIMEOUT_MS = 2000;

/** @brief Schwellwert für Frequenzänderung (Hz), unter dem als konstant gilt */
const float FREQUENCY_CHANGE_THRESHOLD = 0.05f;

/** @brief Zeitpunkt der letzten signifikanten Frequenzänderung */
uint32_t lastFrequencyChangeMs = 0;

/** @brief Letzte gemessene Frequenz für Änderungserkennung */
float lastFrequency = 0.0f;

/** @brief Ausgabepuffer für Sensordaten */
char outputBuffer[256];

/** @brief Zusätzlicher Puffer für HTTP-Antworten */
char httpResponseBuffer[512];

// ================================
// INTERRUPT SERVICE ROUTINES
// ================================

/**
 * @brief Interrupt Service Routine für Hall-Sensor
 *
 * Diese Funktion wird bei fallender Flanke des Hall-Sensors aufgerufen.
 * Sie berechnet die Zeitdifferenz zwischen aufeinanderfolgenden Interrupts
 * und sendet diese an eine Queue für die Hauptschleife.
 *
 * @note Diese Funktion läuft im IRAM für maximale Performance
 * @note Verwendet eine Totzeit zur Entprellung des Signals
 */
void IRAM_ATTR hallSensorInterruptHandler()
{
  uint32_t currentTimeUs = micros();
  uint32_t timeDifferenceUs = currentTimeUs - lastInterruptTimeUs;

  // Prüfe Totzeit zur Entprellung
  if (timeDifferenceUs >= interruptDeadtimeUs)
  {
    interruptPeriodUs = timeDifferenceUs;
    lastInterruptTimeUs = currentTimeUs;

    // Sende Zeitdifferenz an Queue (thread-sicher)
    xQueueSendFromISR(interruptQueue, &timeDifferenceUs, NULL);
  }
}

// ================================
// UTILITY FUNCTIONS
// ================================

/**
 * @brief Gibt den aktuellen WiFi-Status auf der seriellen Schnittstelle aus
 *
 * Zeigt SSID, IP-Adresse und Verbindungsstatus an.
 */
void printWiFiStatus()
{
  Serial.println("========== WiFi Status ==========");
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  IPAddress localIP = WiFi.localIP();
  Serial.print("IP-Adresse: ");
  Serial.println(localIP);

  Serial.print("Gateway: ");
  Serial.println(WiFi.gatewayIP());

  Serial.print("Signalstärke: ");
  Serial.print(WiFi.RSSI());
  Serial.println(" dBm");
  Serial.println("=================================");
}

/**
 * @brief Gibt den aktuellen WiFi-Access Point Status aus
 */
void printWiFiAPStatus()
{
  Serial.println("========== WiFi Access Point Status ==========");
  Serial.printf("SSID: %s\n", WIFI_AP_SSID);
  Serial.printf("IP-Adresse: %s\n", WiFi.softAPIP().toString().c_str());
  Serial.printf("MAC-Adresse: %s\n", WiFi.softAPmacAddress().c_str());
  Serial.printf("Verbundene Clients: %d\n", WiFi.softAPgetStationNum());
  Serial.println("=============================================");
}

/**
 * @brief Initialisiert den LSM6DS3-Sensor über SPI
 *
 * Konfiguriert SPI-Interface und Sensorparameter:
 * - Beschleunigungsbereich: ±2G
 * - Gyroskopmessbereich: ±250 DPS
 *
 * @return true bei erfolgreicher Initialisierung, sonst Endlosschleife
 */
bool initializeLSM6DS3Sensor()
{
  Serial.println("Initialisiere LSM6DS3-Sensor...");

  // SPI-Interface konfigurieren
  SPI.begin(LSM_SCK, LSM_MISO, LSM_MOSI, LSM_CS);

  // Sensor initialisieren
  if (!lsm6ds33.begin_SPI(LSM_CS))
  {
    Serial.println("FEHLER: LSM6DS3-Sensor nicht gefunden!");
    Serial.println("Prüfen Sie die SPI-Verbindungen:");
    Serial.printf("  CS: Pin %d\n", LSM_CS);
    Serial.printf("  SCK: Pin %d\n", LSM_SCK);
    Serial.printf("  MISO: Pin %d\n", LSM_MISO);
    Serial.printf("  MOSI: Pin %d\n", LSM_MOSI);
    return false;
  }

  // Sensor-Parameter konfigurieren
  lsm6ds33.setAccelRange(LSM6DS_ACCEL_RANGE_2_G);
  lsm6ds33.setGyroRange(LSM6DS_GYRO_RANGE_250_DPS);

  Serial.println("LSM6DS3-Sensor erfolgreich initialisiert!");
  Serial.println("  Beschleunigungsbereich: ±2G");
  Serial.println("  Gyroskopmessbereich: ±250 DPS");

  return true;
}

/**
 * @brief Initialisiert die WiFi-Verbindung als Access Point oder Station
 *
 * Je nach Konfiguration wird entweder ein Access Point erstellt oder
 * eine Verbindung zu einem bestehenden Netzwerk hergestellt.
 *
 * @param waitForConnection true = warten auf Verbindung (nur im Station-Modus)
 * @return true bei erfolgreicher Initialisierung
 */
bool initializeWiFiConnection(bool waitForConnection = true)
{
  if (WIFI_AP_MODE)
  {
    // ========== Access Point Modus ==========
    Serial.println("Initialisiere WiFi Access Point...");
    Serial.printf("AP SSID: %s\n", WIFI_AP_SSID);

    // WiFi-Modus auf Access Point setzen
    WiFi.mode(WIFI_AP);

    // Access Point konfigurieren
    if (!WiFi.softAPConfig(AP_IP, AP_GATEWAY, AP_SUBNET))
    {
      Serial.println("FEHLER: Access Point IP-Konfiguration fehlgeschlagen!");
      return false;
    }

    // Access Point starten
    bool apStarted = WiFi.softAP(WIFI_AP_SSID, WIFI_AP_PASSWORD);
    if (!apStarted)
    {
      Serial.println("FEHLER: Access Point konnte nicht gestartet werden!");
      Serial.println("Mögliche Ursachen:");
      Serial.println("  - SSID zu kurz (min. 1 Zeichen)");
      Serial.println("  - Passwort zu kurz (min. 8 Zeichen für WPA)");
      return false;
    }

    Serial.println("Access Point erfolgreich gestartet!");
    Serial.printf("  SSID: %s\n", WIFI_AP_SSID);
    Serial.printf("  IP-Adresse: %s\n", WiFi.softAPIP().toString().c_str());
    Serial.printf("  MAC-Adresse: %s\n", WiFi.softAPmacAddress().c_str());

    // Kurz warten bis AP vollständig aktiv ist
    delay(1000);
  }
  else
  {
    // ========== Station Modus (Verbindung zu bestehendem Netzwerk) ==========
    Serial.println("Initialisiere WiFi Station-Modus...");
    Serial.printf("SSID: %s\n", WIFI_AP_SSID);

    // WiFi-Verbindung starten
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_AP_SSID, WIFI_AP_PASSWORD);

    // WiFi-Energiesparmodus deaktivieren für stabile Verbindung
    WiFi.setSleep(false);

    if (waitForConnection)
    {
      // Warten auf Verbindung
      Serial.print("Verbindungsaufbau");
      int attempts = 0;
      const int maxAttempts = 30; // 30 Sekunden Timeout

      while (WiFi.status() != WL_CONNECTED && attempts < maxAttempts)
      {
        delay(1000);
        Serial.print(".");
        attempts++;
      }

      if (WiFi.status() != WL_CONNECTED)
      {
        Serial.println("\nFEHLER: WiFi-Verbindung nicht möglich!");
        return false;
      }

      Serial.println("\nWiFi-Verbindung erfolgreich hergestellt!");
    }
    else
    {
      Serial.println("WiFi-Verbindung im Hintergrund gestartet (kein Warten)");
    }
  }

  // Server starten
  wifiServer.begin();
  Serial.printf("HTTP-Server gestartet auf Port %d\n", HTTP_SERVER_PORT);

  // UDP-Socket initialisieren
  if (udpSocket.begin(UDP_PORT))
  {
    Serial.printf("UDP-Socket gestartet auf Port %d\n", UDP_PORT);
  }
  else
  {
    Serial.println("FEHLER: UDP-Socket konnte nicht gestartet werden!");
  }

  // Status ausgeben
  if (WIFI_AP_MODE)
  {
    printWiFiAPStatus();
  }
  else if (WiFi.status() == WL_CONNECTED)
  {
    printWiFiStatus();
  }

  return true;
}

/**
 * @brief Fügt einen UDP-Client zur Unicast-Liste hinzu
 *
 * @param clientIP IP-Adresse des Clients
 */
void addUDPClient(IPAddress clientIP)
{
  // Prüfe ob Client bereits in der Liste ist
  for (int i = 0; i < udpClientCount; i++)
  {
    if (udpClientIPs[i] == clientIP)
    {
      return; // Client bereits in der Liste
    }
  }

  // Füge neuen Client hinzu (falls Platz vorhanden)
  if (udpClientCount < 5)
  {
    udpClientIPs[udpClientCount] = clientIP;
    udpClientCount++;
    Serial.printf("UDP-Client hinzugefügt: %s (Total: %d)\n",
                  clientIP.toString().c_str(), udpClientCount);
  }
  else
  {
    Serial.println("WARNUNG: Maximale Anzahl UDP-Clients erreicht!");
  }
}

/**
 * @brief Verarbeitet eingehende UDP-Pakete und registriert Clients
 */
void handleUDPClients()
{
  int packetSize = udpSocket.parsePacket();
  if (packetSize)
  {
    IPAddress remoteIP = udpSocket.remoteIP();

    // Lese das Paket (auch wenn wir den Inhalt ignorieren)
    char incomingPacket[255];
    int len = udpSocket.read(incomingPacket, 255);
    if (len > 0)
    {
      incomingPacket[len] = 0;
    }

    // Füge Client zur Liste hinzu
    addUDPClient(remoteIP);

    if (isDebugMode)
    {
      Serial.printf("DEBUG: UDP-Registrierung von %s, Paket: %s\n",
                    remoteIP.toString().c_str(), incomingPacket);
    }
  }
}

/**
 * @brief Verarbeitet HTTP-Anfragen von WiFi-Clients
 *
 * Behandelt verschiedene HTTP-Endpunkte:
 * - GET /version - Gibt die Software-Version zurück
 * - GET /device-id - Gibt die OpenBIS-Code/Geräte-ID zurück
 * - GET /info - Gibt alle Geräteinformationen zurück
 * - GET /status - Gibt aktuellen System-Status zurück
 * - Alle anderen Anfragen - Normale Sensordaten
 *
 * @param client Der verbundene WiFi-Client
 * @param request Die HTTP-Anfrage als String
 */
void handleHTTPRequest(WiFiClient &client, const String &request)
{
  // HTTP-Response-Header
  const char *httpHeader = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n";

  if (request.indexOf("GET /version") >= 0)
  {
    // Version abfragen
    client.print(httpHeader);
    client.print(SOFTWARE_VERSION);
    Serial.printf("WiFi-Client fragte Version ab: %s\n", SOFTWARE_VERSION);
  }
  else if (request.indexOf("GET /device-id") >= 0)
  {
    // OpenBIS-Code/Geräte-ID abfragen
    client.print(httpHeader);
    client.print(DEVICE_ID);
    Serial.printf("WiFi-Client fragte Device-ID ab: %s\n", DEVICE_ID);
  }
  else if (request.indexOf("GET /info") >= 0)
  {
    // Vollständige Geräteinformationen
    client.print(httpHeader);
    client.printf("Device-ID: %s\n", DEVICE_ID);
    client.printf("Software-Version: %s\n", SOFTWARE_VERSION);
    client.printf("Uptime: %lu ms\n", millis());
    client.printf("WiFi-Status: %s\n", WIFI_AP_MODE ? "Access Point" : (WiFi.status() == WL_CONNECTED ? "Verbunden" : "Getrennt"));
    client.printf("IP-Adresse: %s\n", WIFI_AP_MODE ? WiFi.softAPIP().toString().c_str() : WiFi.localIP().toString().c_str());
    client.printf("Debug-Modus: %s\n", isDebugMode ? "Aktiviert" : "Deaktiviert");
    Serial.println("WiFi-Client fragte vollständige Geräteinformationen ab");
  }
  else if (request.indexOf("GET /status") >= 0)
  {
    // System-Status
    client.print(httpHeader);
    client.printf("Uptime: %lu ms\n", millis());
    client.printf("Aktuelle-Frequenz: %.4f Hz\n", currentFrequency);
    client.printf("Freier-Heap: %d Bytes\n", ESP.getFreeHeap());
    client.printf("WiFi-Signalstärke: %s\n", WIFI_AP_MODE ? "N/A (Access Point)" : String(WiFi.RSSI() + " dBm").c_str());
    Serial.println("WiFi-Client fragte System-Status ab");
  }
  else
  {
    // Standard-Sensordaten senden (für normale Datenabfrage)
    client.print(httpHeader);
    client.print(outputBuffer);
  }

  client.flush();
}

// ================================
// MAIN PROGRAM FUNCTIONS
// ================================

/**
 * @brief Setup-Funktion - wird einmal beim Start ausgeführt
 *
 * Initialisiert alle Systemkomponenten:
 * - Serielle Kommunikation
 * - Debug-Modus Erkennung
 * - Hall-Sensor mit Interrupt
 * - LSM6DS3-Sensor
 * - WiFi-Verbindung (auch im Debug-Modus)
 * - Status-LED
 */
void setup()
{
  // ========== Serielle Kommunikation initialisieren ==========
  Serial.begin(115200);

  // Warte kurz auf serielle Verbindung für Debug-Modus
  unsigned long serialWaitStart = millis();
  const unsigned long SERIAL_WAIT_TIMEOUT = 3000; // 3 Sekunden

  while (!Serial && (millis() - serialWaitStart) < SERIAL_WAIT_TIMEOUT)
  {
    delay(10);
  }

  // ========== Debug-Modus Erkennung ==========
  if (Serial)
  {
    isDebugMode = true;
    Serial.println("==========================================");
    Serial.println("  GYROSCOPE DATA ACQUISITION SYSTEM");
    Serial.printf("  Device ID: %s\n", DEVICE_ID);
    Serial.printf("  Software Version: %s\n", SOFTWARE_VERSION);
    Serial.println("  Debug-Modus: AKTIVIERT");
    Serial.println("==========================================");
  }

  // ========== WiFi-SSID generieren ==========
  snprintf(WIFI_AP_SSID, sizeof(WIFI_AP_SSID), "Kreisel-%s", DEVICE_ID);
  Serial.printf("WiFi-SSID generiert: %s\n", WIFI_AP_SSID);

  // ========== Interrupt-Queue initialisieren ==========
  interruptQueue = xQueueCreate(8, sizeof(uint32_t));
  if (interruptQueue == NULL)
  {
    Serial.println("FEHLER: Interrupt-Queue konnte nicht erstellt werden!");
    while (1)
      delay(100);
  }

  lastInterruptTimeUs = micros();

  // ========== Hall-Sensor konfigurieren ==========
  Serial.println("Konfiguriere Hall-Sensor...");
  pinMode(HALL_DIGITAL_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(HALL_DIGITAL_PIN),
                  hallSensorInterruptHandler, FALLING);
  Serial.printf("Hall-Sensor an Pin %d konfiguriert (Interrupt bei fallender Flanke)\n",
                HALL_DIGITAL_PIN);

  // ========== Status-LED konfigurieren ==========
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println("Status-LED konfiguriert");

  // ========== LSM6DS3-Sensor initialisieren ==========
  if (!initializeLSM6DS3Sensor())
  {
    Serial.println("KRITISCHER FEHLER: Sensor-Initialisierung fehlgeschlagen!");
    while (1)
    {
      digitalWrite(LED_BUILTIN, HIGH);
      delay(200);
      digitalWrite(LED_BUILTIN, LOW);
      delay(200);
    }
  }

  // ========== WiFi initialisieren ==========
  // WICHTIGE ÄNDERUNG: WiFi wird auch im Debug-Modus initialisiert,
  // aber ohne auf Client-Verbindungen zu warten
  if (isDebugMode)
  {
    Serial.println("Debug-Modus: WiFi wird initialisiert, aber nicht auf Clients gewartet");
    initializeWiFiConnection(false); // Nicht auf Verbindung warten
  }
  else
  {
    Serial.println("Produktions-Modus: WiFi wird vollständig initialisiert");
    if (!initializeWiFiConnection(true))
    { // Auf Verbindung warten
      Serial.println("WARNUNG: WiFi-Initialisierung fehlgeschlagen!");
    }
  }

  // ========== Setup abgeschlossen ==========
  Serial.println("==========================================");
  Serial.println("Setup abgeschlossen - System bereit!");

  if (WIFI_AP_MODE || WiFi.status() == WL_CONNECTED)
  {
    Serial.println("\nVerfügbare Schnittstellen:");
    IPAddress serverIP = WIFI_AP_MODE ? WiFi.softAPIP() : WiFi.localIP();

    // HTTP-API Endpunkte
    Serial.println("HTTP-API:");
    Serial.printf("  http://%s/version    - Software-Version\n", serverIP.toString().c_str());
    Serial.printf("  http://%s/device-id  - OpenBIS-Code/Geräte-ID\n", serverIP.toString().c_str());
    Serial.printf("  http://%s/info       - Geräteinformationen\n", serverIP.toString().c_str());
    Serial.printf("  http://%s/status     - System-Status\n", serverIP.toString().c_str());

    // Sensordaten-Schnittstellen
    Serial.println("Sensordaten:");
    if (USE_UDP_FOR_DATA)
    {
      if (USE_UDP_BROADCAST)
      {
        Serial.printf("  UDP-Broadcast: %s:%d (automatisch)\n", UDP_BROADCAST_IP.toString().c_str(), UDP_PORT);
        Serial.printf("  UDP-Empfang: socat udp-recv:%d -\n", UDP_PORT);
      }
      else
      {
        Serial.printf("  UDP-Unicast: Port %d (Client-Registrierung erforderlich)\n", UDP_PORT);
        Serial.printf("  Registrierung: echo 'register' | nc -u %s %d\n", serverIP.toString().c_str(), UDP_PORT);
        Serial.printf("  Empfang: nc -u -l %d\n", UDP_PORT);
      }
    }
    else
    {
      Serial.printf("  TCP-Stream: nc %s %d\n", serverIP.toString().c_str(), HTTP_SERVER_PORT);
    }

    if (WIFI_AP_MODE)
    {
      Serial.println("\nVerbindung zum Access Point:");
      Serial.printf("  1. WiFi-Netzwerk '%s' suchen\n", WIFI_AP_SSID);
      Serial.printf("  2. Mit Passwort '%s' verbinden\n", WIFI_AP_PASSWORD);
      Serial.printf("  3. Auf Sensordaten lauschen oder API verwenden\n");
    }
  }

  Serial.println("==========================================");

  if (isDebugMode)
  {
    Serial.println("Datenformat: Zeitstempel,Frequenz,Accel_X,Accel_Y,Accel_Z,Gyro_X,Gyro_Y,Gyro_Z");
    Serial.printf("Übertragungsmodus: %s (%s)\n",
                  USE_UDP_FOR_DATA ? "UDP" : "TCP",
                  USE_UDP_FOR_DATA ? (USE_UDP_BROADCAST ? "Broadcast" : "Unicast") : "Point-to-Point");
    Serial.println("HTTP-API auch im Debug-Modus verfügbar");
  }

  // Status-LED einschalten = System bereit
  digitalWrite(LED_BUILTIN, HIGH);
}

/**
 * @brief Hauptschleife - wird kontinuierlich ausgeführt
 *
 * Führt folgende Aufgaben aus:
 * 1. Sensordaten vom LSM6DS3 lesen
 * 2. Hall-Sensor Interrupt-Daten verarbeiten
 * 3. Datenpaket formatieren
 * 4. WiFi-Clients bedienen (sowohl Debug- als auch Produktions-Modus)
 * 5. Im Debug-Modus zusätzlich serielle Ausgabe
 */
void loop()
{
  // ========== Sensordaten lesen ==========
  sensors_event_t accelerationEvent, gyroscopeEvent, temperatureEvent;
  lsm6ds33.getEvent(&accelerationEvent, &gyroscopeEvent, &temperatureEvent);

  // ========== Hall-Sensor Interrupt-Daten verarbeiten ==========
  uint32_t interruptTimeDelta;
  if (xQueueReceive(interruptQueue, &interruptTimeDelta, 0) == pdTRUE)
  {
    // Neue Interrupt-Daten verfügbar
    if (interruptTimeDelta > 0)
    {
      float newFrequency = 1000000.0f / (float)interruptTimeDelta;
      
      // Prüfe ob signifikante Frequenzänderung vorliegt
      if (abs(newFrequency - lastFrequency) > FREQUENCY_CHANGE_THRESHOLD)
      {
        // Signifikante Änderung erkannt - Timer zurücksetzen
        lastFrequencyChangeMs = millis();
        lastFrequency = newFrequency;
        
        if (isDebugMode)
        {
          Serial.printf("DEBUG: Frequenzänderung erkannt: %.4f Hz -> %.4f Hz\n", 
                        lastFrequency, newFrequency);
        }
      }
      
      currentFrequency = newFrequency;
    }
  }
  
  // ========== Frequenz-Konstanz-Überprüfung ==========
  // Wenn Frequenz über definierte Zeit konstant ist, setze auf 0
  if (currentFrequency > 0.0f)
  {
    uint32_t timeSinceLastChange = millis() - lastFrequencyChangeMs;
    
    if (timeSinceLastChange > FREQUENCY_STABLE_TIMEOUT_MS)
    {
      if (isDebugMode)
      {
        Serial.printf("DEBUG: Frequenz seit %lu ms konstant bei %.4f Hz - setze auf 0\n",
                      timeSinceLastChange, currentFrequency);
      }
      
      currentFrequency = 0.0f;
      lastFrequency = 0.0f;
    }
  }

  // ========== Datenpaket formatieren ==========
  // Format: Zeitstempel,Frequenz,Accel_X,Accel_Y,Accel_Z,Gyro_X,Gyro_Y,Gyro_Z
  snprintf(outputBuffer, sizeof(outputBuffer),
           "%lu,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f",
           (unsigned long)millis(),
           currentFrequency,
           accelerationEvent.acceleration.x,
           accelerationEvent.acceleration.y,
           accelerationEvent.acceleration.z,
           gyroscopeEvent.gyro.x,
           gyroscopeEvent.gyro.y,
           gyroscopeEvent.gyro.z);

  // ========== Datenausgabe ==========

  // HTTP-API über TCP (immer verfügbar)
  WiFiClient httpClient = wifiServer.available();
  if (httpClient && httpClient.connected())
  {
    if (httpClient.available())
    {
      String httpRequest = httpClient.readStringUntil('\r');
      httpClient.readStringUntil('\n');

      while (httpClient.available())
      {
        httpClient.read();
      }

      if (httpRequest.length() > 0)
      {
        handleHTTPRequest(httpClient, httpRequest);
        if (isDebugMode)
        {
          Serial.printf("DEBUG: HTTP-Request verarbeitet: %s\n", httpRequest.c_str());
        }
      }
    }
    httpClient.stop();
  }

  // Sensordatenübertragung - UDP oder TCP
  if (USE_UDP_FOR_DATA)
  {
    // ========== UDP-Client-Verwaltung ==========
    // Prüfe auf eingehende UDP-Pakete zur Client-Registrierung
    handleUDPClients();

    // ========== UDP-Datenübertragung ==========
    if (USE_UDP_BROADCAST)
    {
      // Broadcast an alle Clients im Netzwerk
      udpSocket.beginPacket(UDP_BROADCAST_IP, UDP_PORT);
      udpSocket.println(outputBuffer); // println für Newline
      udpSocket.endPacket();

      if (isDebugMode)
      {
        Serial.printf("DEBUG: UDP-Broadcast gesendet: %s\n", outputBuffer);
      }
    }
    else
    {
      // Unicast an registrierte Clients
      for (int i = 0; i < udpClientCount; i++)
      {
        udpSocket.beginPacket(udpClientIPs[i], UDP_PORT);
        udpSocket.println(outputBuffer); // println für Newline
        udpSocket.endPacket();
      }

      if (isDebugMode && udpClientCount > 0)
      {
        Serial.printf("DEBUG: UDP-Unicast an %d Clients gesendet: %s\n",
                      udpClientCount, outputBuffer);
      }
    }
  }
  else
  {
    // ========== TCP-Übertragung (Legacy) ==========
    // Prüfe auf neue Client-Verbindungen
    if (!persistentClient || !persistentClient.connected())
    {
      WiFiClient newClient = wifiServer.available();
      if (newClient)
      {
        persistentClient = newClient;
        if (isDebugMode)
        {
          Serial.println("DEBUG: Neuer TCP-Client für Sensordaten verbunden");
        }
      }
    }

    // Behandle aktiven TCP-Client
    if (persistentClient && persistentClient.connected())
    {
      if (!persistentClient.available())
      {
        // Keine HTTP-Daten - sende kontinuierlich Sensordaten
        persistentClient.println(outputBuffer);
        persistentClient.flush();
        if (isDebugMode)
        {
          Serial.printf("DEBUG: TCP-Sensordaten gesendet: %s\n", outputBuffer);
        }
      }
    }
  }

  // ========== Timing ==========
  delay(10); // 100 Hz Datenrate
}
