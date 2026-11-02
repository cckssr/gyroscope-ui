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
#include <ArduinoOTA.h>
#include <esp_wifi.h>
#include "secrets.h"

#ifndef SECRET_OTA_PASS
#error "Define SECRET_OTA_PASS in src/secrets.h (see secrets_template.h)"
#endif

// ================================
// SYSTEM CONFIGURATION
// ================================

/** @brief Gerätekennzeichnung für Identifikation (gesetzt via build_flags: -DDEVICE_ID_STR=...) */
#ifndef DEVICE_ID_STR
#define DEVICE_ID_STR "UNKNOWN"
#endif
const char *DEVICE_ID = DEVICE_ID_STR;

/** @brief Software-Versionsnummer */
const char *SOFTWARE_VERSION = "2.0.0";

/** @brief Wire protocol version (9-field data line with sequence number, see docs/PROTOCOL.md) */
const int PROTOCOL_VERSION = 2;

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

/** @brief A router network the station side joins for OTA updates */
struct StaNetwork
{
  const char *ssid;
  const char *password;
};

/** @brief Known router networks for OTA; the second one is optional (SECRET_STA_SSID2 / SECRET_STA_PASS2) */
const StaNetwork STA_NETWORKS[] = {
    {SECRET_STA_SSID, SECRET_STA_PASS},
#if defined(SECRET_STA_SSID2) && defined(SECRET_STA_PASS2)
    {SECRET_STA_SSID2, SECRET_STA_PASS2},
#endif
};

/** @brief Number of entries in STA_NETWORKS */
const size_t STA_NETWORK_COUNT = sizeof(STA_NETWORKS) / sizeof(STA_NETWORKS[0]);

/** @brief The router network chosen at boot (see chooseStaNetwork) */
const StaNetwork *selectedStaNetwork = &STA_NETWORKS[0];
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

/** @brief One registered UDP data receiver (host) */
struct UdpClient
{
  IPAddress ip;        ///< Destination IP (always the datagram's source IP)
  uint16_t port;       ///< Destination port (from the CONNECT payload, else the source port)
  uint32_t lastSeenMs; ///< millis() of the last registration datagram
};

/** @brief Maximum number of simultaneously served UDP clients */
const int MAX_UDP_CLIENTS = 5;

/** @brief A client is dropped after this time without a registration (the host re-sends CONNECT every 2 s) */
const uint32_t CLIENT_TIMEOUT_MS = 10000;

/** @brief Maximum number of datagrams drained per loop pass (keeps the loop non-blocking) */
const int MAX_UDP_PACKETS_PER_PASS = 8;

/** @brief Table of live UDP clients; entries [0, udpClientCount) are valid */
UdpClient udpClients[MAX_UDP_CLIENTS];
int udpClientCount = 0;

/** @brief Sequence number of the next data line (starts at 0 at boot, wraps naturally) */
uint32_t sequenceNumber = 0;

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
// FREQUENCY PULSE TIMEOUT
// ================================

/** @brief Minimum time without a Hall pulse before the frequency is reported as 0 Hz */
const uint32_t PULSE_TIMEOUT_MIN_MS = 2000;

/** @brief The pulse timeout is at least this many periods of the last measured pulse period */
const uint32_t PULSE_TIMEOUT_PERIODS = 3;

/** @brief millis() of the last processed Hall pulse (loop() only) */
uint32_t lastPulseMs = 0;

/** @brief Period of the last processed Hall pulse in microseconds (loop() only) */
uint32_t lastPulsePeriodUs = 0;

/** @brief true once a Hall pulse with a valid period has been processed (loop() only) */
bool pulseSeen = false;

/** @brief true once the first queued pulse has been discarded (its period is measured from boot, not from a pulse) */
bool firstPulseDiscarded = false;

// ================================
// WIFI DEBUG VARIABLES
// ================================

/** @brief Anzahl der verbundenen Clients beim letzten Check */
int lastConnectedClients = 0;

/** @brief Zeitpunkt des letzten WiFi-Status-Prints */
uint32_t lastWiFiStatusPrintMs = 0;

/** @brief Intervall für periodische WiFi-Status-Ausgabe (ms) */
const uint32_t WIFI_STATUS_PRINT_INTERVAL_MS = 10000; // 10 Sekunden

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
  Serial.printf("Passwort: %s\n", WIFI_AP_PASSWORD);
  Serial.printf("Kanal: %d\n", WiFi.channel());
  Serial.printf("IP-Adresse: %s\n", WiFi.softAPIP().toString().c_str());
  Serial.printf("Gateway: %s\n", AP_GATEWAY.toString().c_str());
  Serial.printf("Subnet: %s\n", AP_SUBNET.toString().c_str());
  Serial.printf("MAC-Adresse: %s\n", WiFi.softAPmacAddress().c_str());
  Serial.printf("Verbundene Clients: %d\n", WiFi.softAPgetStationNum());
  Serial.printf("Max. Verbindungen: 4 (Standard ESP32)\n");
  Serial.println("=============================================");
}

/**
 * @brief WiFi-Event-Handler für Access Point Events
 *
 * Wird aufgerufen bei Client-Verbindungen und -Trennungen
 *
 * @param event WiFi-Event-Type
 * @param info Event-Informationen
 */
void onWiFiEvent(WiFiEvent_t event, WiFiEventInfo_t info)
{
  switch (event)
  {
  case ARDUINO_EVENT_WIFI_AP_START:
    Serial.println("[WiFi-Event] Access Point gestartet");
    Serial.printf("[WiFi-Event] Warte auf Client-Verbindungen...\n");
    break;

  case ARDUINO_EVENT_WIFI_AP_STOP:
    Serial.println("[WiFi-Event] Access Point gestoppt");
    break;

  case ARDUINO_EVENT_WIFI_AP_STACONNECTED:
    Serial.println("\n========== CLIENT VERBUNDEN ==========");
    Serial.printf("[WiFi-Event] Neuer Client verbunden!\n");
    Serial.printf("[WiFi-Event] MAC-Adresse: %02X:%02X:%02X:%02X:%02X:%02X\n",
                  info.wifi_ap_staconnected.mac[0],
                  info.wifi_ap_staconnected.mac[1],
                  info.wifi_ap_staconnected.mac[2],
                  info.wifi_ap_staconnected.mac[3],
                  info.wifi_ap_staconnected.mac[4],
                  info.wifi_ap_staconnected.mac[5]);
    Serial.printf("[WiFi-Event] AID (Association ID): %d\n", info.wifi_ap_staconnected.aid);
    Serial.printf("[WiFi-Event] Gesamtanzahl Clients: %d\n", WiFi.softAPgetStationNum());
    Serial.println("======================================\n");
    break;

  case ARDUINO_EVENT_WIFI_AP_STADISCONNECTED:
    Serial.println("\n========== CLIENT GETRENNT ==========");
    Serial.printf("[WiFi-Event] Client getrennt\n");
    Serial.printf("[WiFi-Event] MAC-Adresse: %02X:%02X:%02X:%02X:%02X:%02X\n",
                  info.wifi_ap_stadisconnected.mac[0],
                  info.wifi_ap_stadisconnected.mac[1],
                  info.wifi_ap_stadisconnected.mac[2],
                  info.wifi_ap_stadisconnected.mac[3],
                  info.wifi_ap_stadisconnected.mac[4],
                  info.wifi_ap_stadisconnected.mac[5]);
    Serial.printf("[WiFi-Event] AID (Association ID): %d\n", info.wifi_ap_stadisconnected.aid);
    Serial.printf("[WiFi-Event] Verbleibende Clients: %d\n", WiFi.softAPgetStationNum());
    Serial.println("\nMÖGLICHE TRENNUNGSGRÜNDE:");
    Serial.println("  1. Keine IP-Adresse vom DHCP-Server erhalten");
    Serial.println("  2. Client erwartet Internet-Verbindung");
    Serial.println("  3. Schwaches Signal (RSSI < -70 dBm)");
    Serial.println("  4. Client-Timeout oder manuelle Trennung");
    Serial.println("  5. Authentifizierungs-Problem");
    Serial.println("\nLÖSUNGSVERSUCHE:");
    Serial.println("  - DHCP auf Client deaktivieren, manuelle IP setzen:");
    Serial.println("    IP: 192.168.4.2, Subnet: 255.255.255.0, Gateway: 192.168.4.1");
    Serial.println("  - 'Auto-Join' für dieses Netzwerk deaktivieren");
    Serial.println("  - Auf Mac: Captive Portal deaktivieren");
    Serial.println("=====================================\n");
    break;

  case ARDUINO_EVENT_WIFI_AP_PROBEREQRECVED:
    // Probe Request = Client sucht nach verfügbaren Netzwerken
    if (isDebugMode)
    {
      Serial.printf("[WiFi-Event] Probe Request von: %02X:%02X:%02X:%02X:%02X:%02X (RSSI: %d dBm)\n",
                    info.wifi_ap_probereqrecved.mac[0],
                    info.wifi_ap_probereqrecved.mac[1],
                    info.wifi_ap_probereqrecved.mac[2],
                    info.wifi_ap_probereqrecved.mac[3],
                    info.wifi_ap_probereqrecved.mac[4],
                    info.wifi_ap_probereqrecved.mac[5],
                    info.wifi_ap_probereqrecved.rssi);
    }
    break;

  case ARDUINO_EVENT_WIFI_STA_CONNECTED:
    Serial.printf("[WiFi-Event] Router verbunden (SSID: %s)\n", selectedStaNetwork->ssid);
    break;

  case ARDUINO_EVENT_WIFI_STA_GOT_IP:
    Serial.printf("[WiFi-Event] Router IP erhalten: %s (OTA verfügbar)\n",
                  WiFi.localIP().toString().c_str());
    break;

  case ARDUINO_EVENT_WIFI_STA_DISCONNECTED:
    Serial.printf("[WiFi-Event] Router-Verbindung getrennt - OTA nicht verfügbar\n");
    break;

  default:
    if (isDebugMode)
    {
      Serial.printf("[WiFi-Event] Unbekanntes Event: %d\n", event);
    }
    break;
  }
}

/**
 * @brief Gibt detaillierte Informationen über verbundene Clients aus
 */
void printConnectedClients()
{
  wifi_sta_list_t stationList;
  esp_wifi_ap_get_sta_list(&stationList);

  Serial.println("\n========== VERBUNDENE CLIENTS ==========");
  Serial.printf("Anzahl: %d\n", stationList.num);

  if (stationList.num > 0)
  {
    Serial.println("\nClient-Details:");
    for (int i = 0; i < stationList.num; i++)
    {
      Serial.printf("  Client %d:\n", i + 1);
      Serial.printf("    MAC: %02X:%02X:%02X:%02X:%02X:%02X\n",
                    stationList.sta[i].mac[0],
                    stationList.sta[i].mac[1],
                    stationList.sta[i].mac[2],
                    stationList.sta[i].mac[3],
                    stationList.sta[i].mac[4],
                    stationList.sta[i].mac[5]);
      Serial.printf("    RSSI: %d dBm\n", stationList.sta[i].rssi);
    }
  }
  else
  {
    Serial.println("  Keine Clients verbunden");
  }

  Serial.println("========================================\n");
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
 * @brief Chooses the router network for OTA
 *
 * With one known network it is used directly. With two, a single scan at boot picks the
 * strongest known network that is in range; if none is found, the first one is used (the
 * station keeps retrying it in the background, as before). Scanning only once at boot keeps
 * the access point on a stable channel while students are connected.
 *
 * @return Entry of STA_NETWORKS to connect to
 */
const StaNetwork *chooseStaNetwork()
{
  if (STA_NETWORK_COUNT == 1)
  {
    return &STA_NETWORKS[0];
  }

  Serial.println("Scanning for known router networks...");
  const int found = WiFi.scanNetworks();
  const StaNetwork *best = NULL;
  int32_t bestRssi = INT32_MIN;
  for (int i = 0; i < found; i++)
  {
    for (size_t k = 0; k < STA_NETWORK_COUNT; k++)
    {
      if (WiFi.SSID(i) == STA_NETWORKS[k].ssid && WiFi.RSSI(i) > bestRssi)
      {
        best = &STA_NETWORKS[k];
        bestRssi = WiFi.RSSI(i);
      }
    }
  }
  WiFi.scanDelete();

  if (best == NULL)
  {
    Serial.println("No known router network in range, using the first one");
    return &STA_NETWORKS[0];
  }
  Serial.printf("Router network chosen: %s (RSSI: %ld dBm)\n", best->ssid, (long)bestRssi);
  return best;
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
    Serial.printf("AP Passwort: %s\n", WIFI_AP_PASSWORD);
    Serial.printf("AP Passwort-Länge: %d Zeichen\n", strlen(WIFI_AP_PASSWORD));

    // WiFi-Event-Handler registrieren
    WiFi.onEvent(onWiFiEvent);
    Serial.println("WiFi-Event-Handler registriert");

    // WiFi-Modus auf Access Point + Station setzen (für OTA über Router)
    WiFi.mode(WIFI_AP_STA);

    // Access Point konfigurieren
    if (!WiFi.softAPConfig(AP_IP, AP_GATEWAY, AP_SUBNET))
    {
      Serial.println("FEHLER: Access Point IP-Konfiguration fehlgeschlagen!");
      return false;
    }

    // Access Point starten mit erweiterten Parametern
    // Parameter: SSID, Password, Channel, Hidden, Max Connections
    bool apStarted = WiFi.softAP(WIFI_AP_SSID, WIFI_AP_PASSWORD, 1, 0, 4);
    if (!apStarted)
    {
      Serial.println("FEHLER: Access Point konnte nicht gestartet werden!");
      Serial.println("Mögliche Ursachen:");
      Serial.println("  - SSID zu kurz (min. 1 Zeichen)");
      Serial.println("  - Passwort zu kurz (min. 8 Zeichen für WPA)");
      return false;
    }

    Serial.println("DHCP-Server automatisch gestartet (ESP32 Standard)");
    Serial.println("  Standard DHCP-Range: 192.168.4.2 - 192.168.4.254");

    Serial.println("Access Point erfolgreich gestartet!");
    Serial.printf("  SSID: %s\n", WIFI_AP_SSID);
    Serial.printf("  Passwort: %s\n", WIFI_AP_PASSWORD);
    Serial.printf("  Kanal: %d\n", WiFi.channel());
    Serial.printf("  IP-Adresse (Gateway): %s\n", WiFi.softAPIP().toString().c_str());
    Serial.printf("  Subnet-Maske: %s\n", AP_SUBNET.toString().c_str());
    Serial.printf("  MAC-Adresse: %s\n", WiFi.softAPmacAddress().c_str());
    Serial.printf("  Max. Clients: 4\n");
    Serial.printf("  Verschlüsselung: WPA2-PSK\n");

    Serial.println("\n========== MAC-SPEZIFISCHE HINWEISE ==========");
    Serial.println("Wenn Ihr Mac sich nicht verbinden kann:");
    Serial.println("  1. Deaktivieren Sie 'Auto-Join Captive Portals':");
    Serial.println("     Terminal: sudo defaults write /Library/Preferences/SystemConfiguration/com.apple.captive.control.plist Active -bool false");
    Serial.println("  2. Oder setzen Sie manuelle IP-Konfiguration:");
    Serial.println("     IP: 192.168.4.2");
    Serial.println("     Subnet: 255.255.255.0");
    Serial.println("     Router: 192.168.4.1");
    Serial.println("     DNS: 192.168.4.1 (oder leer lassen)");
    Serial.println("  3. Ignorieren Sie 'Kein Internet verfügbar' Warnungen");
    Serial.println("=============================================");

    Serial.println("\n========== VERBINDUNGSANLEITUNG ==========");
    Serial.println("So verbinden Sie sich mit dem Access Point:");
    Serial.println("  1. Öffnen Sie die WiFi-Einstellungen auf Ihrem Gerät");
    Serial.printf("  2. Suchen Sie das Netzwerk '%s'\n", WIFI_AP_SSID);
    Serial.printf("  3. Geben Sie das Passwort ein: %s\n", WIFI_AP_PASSWORD);
    Serial.println("  4. Warten Sie auf die Verbindungsbestätigung");
    Serial.println("==========================================\n");

    // Kurz warten bis AP vollständig aktiv ist
    delay(1000);

    // STA-Verbindung zum Router starten (für OTA), max. 10 Sekunden warten
    selectedStaNetwork = chooseStaNetwork();
    Serial.printf("Verbinde mit Router (SSID: %s)", selectedStaNetwork->ssid);
    WiFi.begin(selectedStaNetwork->ssid, selectedStaNetwork->password);
    {
      int attempts = 0;
      const int maxAttempts = 10;
      while (WiFi.status() != WL_CONNECTED && attempts < maxAttempts)
      {
        delay(1000);
        Serial.print(".");
        attempts++;
      }
    }
    if (WiFi.status() == WL_CONNECTED)
    {
      Serial.printf("\nRouter-Verbindung erfolgreich! IP: %s (OTA verfügbar)\n",
                    WiFi.localIP().toString().c_str());
    }
    else
    {
      Serial.printf("\nRouter-Verbindung fehlgeschlagen (SSID: %s) - OTA nicht verfügbar\n",
                    selectedStaNetwork->ssid);
    }

    Serial.println("Access Point ist nun bereit für Verbindungen!");
    Serial.println("Warte auf Client-Verbindungen...\n");
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

  // OTA initialisieren
  ArduinoOTA.setHostname(WIFI_AP_SSID);
  ArduinoOTA.setPassword(SECRET_OTA_PASS);
  ArduinoOTA.begin();
  Serial.printf("OTA bereit (Hostname: %s)\n", WIFI_AP_SSID);

  return true;
}

/**
 * @brief Parses a registration payload of the form "CONNECT:<ip>:<port>"
 *
 * The <ip> part is deliberately ignored: the host's own guess of its address can be wrong
 * on machines with several network interfaces, so the datagram's source IP is authoritative.
 * Only the port is taken from the payload. Trailing CR/LF/whitespace is allowed.
 *
 * @param payload NUL-terminated payload
 * @param port Receives the port (1..65535) on success
 * @return true if the payload is a well-formed CONNECT message with a valid port
 */
bool parseConnectPort(const char *payload, uint16_t &port)
{
  static const char PREFIX[] = "CONNECT:";
  const size_t prefixLen = sizeof(PREFIX) - 1;
  if (strncmp(payload, PREFIX, prefixLen) != 0)
  {
    return false;
  }

  // The port follows the last ':' (an IPv4 address contains none); there must be a ':' after the prefix.
  const char *portStart = strrchr(payload, ':');
  if (portStart == NULL || portStart < payload + prefixLen)
  {
    return false;
  }
  portStart++;
  if (portStart == payload + prefixLen)
  {
    return false; // "CONNECT:<port>" without an <ip> part
  }

  uint32_t value = 0;
  int digits = 0;
  while (portStart[digits] >= '0' && portStart[digits] <= '9')
  {
    if (digits >= 5)
    {
      return false;
    }
    value = value * 10 + (uint32_t)(portStart[digits] - '0');
    digits++;
  }
  if (digits == 0 || value < 1 || value > 65535)
  {
    return false;
  }

  // Only whitespace may follow the digits
  for (const char *c = portStart + digits; *c != '\0'; c++)
  {
    if (*c != '\r' && *c != '\n' && *c != ' ' && *c != '\t')
    {
      return false;
    }
  }

  port = (uint16_t)value;
  return true;
}

/**
 * @brief Registers a UDP client or refreshes its timestamp
 *
 * Clients are keyed by (ip, port). If the table is full, the entry with the oldest
 * registration is replaced.
 *
 * @param ip Destination IP
 * @param port Destination port
 * @param nowMs Current millis()
 */
void registerUDPClient(const IPAddress &ip, uint16_t port, uint32_t nowMs)
{
  for (int i = 0; i < udpClientCount; i++)
  {
    if (udpClients[i].ip == ip && udpClients[i].port == port)
    {
      udpClients[i].lastSeenMs = nowMs;
      return;
    }
  }

  int slot;
  if (udpClientCount < MAX_UDP_CLIENTS)
  {
    slot = udpClientCount++;
  }
  else
  {
    // Table full: replace the entry that has not been refreshed for the longest time
    slot = 0;
    for (int i = 1; i < udpClientCount; i++)
    {
      if ((uint32_t)(nowMs - udpClients[i].lastSeenMs) > (uint32_t)(nowMs - udpClients[slot].lastSeenMs))
      {
        slot = i;
      }
    }
    Serial.printf("UDP client table full, replacing %s:%u\n",
                  udpClients[slot].ip.toString().c_str(), (unsigned)udpClients[slot].port);
  }

  udpClients[slot].ip = ip;
  udpClients[slot].port = port;
  udpClients[slot].lastSeenMs = nowMs;
  Serial.printf("UDP client registered: %s:%u (total: %d)\n",
                ip.toString().c_str(), (unsigned)port, udpClientCount);
}

/**
 * @brief Removes UDP clients that have not been refreshed within CLIENT_TIMEOUT_MS
 *
 * @param nowMs Current millis()
 */
void expireUDPClients(uint32_t nowMs)
{
  int i = 0;
  while (i < udpClientCount)
  {
    if ((uint32_t)(nowMs - udpClients[i].lastSeenMs) > CLIENT_TIMEOUT_MS)
    {
      Serial.printf("UDP client expired: %s:%u\n",
                    udpClients[i].ip.toString().c_str(), (unsigned)udpClients[i].port);
      for (int j = i + 1; j < udpClientCount; j++)
      {
        udpClients[j - 1] = udpClients[j];
      }
      udpClientCount--;
    }
    else
    {
      i++;
    }
  }
}

/**
 * @brief Drains pending UDP datagrams and registers/refreshes their senders
 *
 * Any datagram on UDP_PORT registers its sender. The destination IP is always the source IP;
 * the destination port is taken from a "CONNECT:<ip>:<port>" payload, else it is the source port.
 * At most MAX_UDP_PACKETS_PER_PASS datagrams are handled per call; never blocks.
 */
void handleUDPClients()
{
  const uint32_t nowMs = millis();
  char payload[64];

  for (int n = 0; n < MAX_UDP_PACKETS_PER_PASS; n++)
  {
    if (udpSocket.parsePacket() <= 0)
    {
      break;
    }

    const IPAddress remoteIP = udpSocket.remoteIP();
    const uint16_t remotePort = udpSocket.remotePort();

    // The payload is bounded; the rest of an oversized datagram is discarded
    int len = udpSocket.read(payload, sizeof(payload) - 1);
    if (len < 0)
    {
      len = 0;
    }
    payload[len] = '\0';

    uint16_t destinationPort = remotePort;
    uint16_t payloadPort = 0;
    if (parseConnectPort(payload, payloadPort))
    {
      destinationPort = payloadPort;
    }

    registerUDPClient(remoteIP, destinationPort, nowMs);

    if (isDebugMode)
    {
      Serial.printf("DEBUG: UDP registration from %s:%u -> %s:%u, payload: %s\n",
                    remoteIP.toString().c_str(), (unsigned)remotePort,
                    remoteIP.toString().c_str(), (unsigned)destinationPort, payload);
    }
  }

  expireUDPClients(nowMs);
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
    client.printf("Protocol: %d\n", PROTOCOL_VERSION);
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
    Serial.println("Datenformat: Zeitstempel,Frequenz,Accel_X,Accel_Y,Accel_Z,Gyro_X,Gyro_Y,Gyro_Z,Sequenz");
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
  ArduinoOTA.handle();

  // ========== WiFi-Client-Monitoring (Access Point Modus) ==========
  if (WIFI_AP_MODE)
  {
    int currentClientCount = WiFi.softAPgetStationNum();

    // Erkenne Client-Änderungen (zusätzlich zum Event-Handler)
    if (currentClientCount != lastConnectedClients)
    {
      Serial.printf("[Monitor] Client-Anzahl ge\u00e4ndert: %d -> %d\n",
                    lastConnectedClients, currentClientCount);
      lastConnectedClients = currentClientCount;

      // Zeige detaillierte Client-Informationen
      if (currentClientCount > 0)
      {
        printConnectedClients();
      }
    }

    // Periodischer WiFi-Status (alle 10 Sekunden) - nur im Debug-Modus
    if (isDebugMode)
    {
      uint32_t currentTime = millis();
      if (currentTime - lastWiFiStatusPrintMs >= WIFI_STATUS_PRINT_INTERVAL_MS)
      {
        lastWiFiStatusPrintMs = currentTime;

        Serial.println("\n========== PERIODISCHER STATUS ==========");
        Serial.printf("Uptime: %lu ms\n", currentTime);
        Serial.printf("Verbundene Clients: %d\n", currentClientCount);
        Serial.printf("UDP-Clients registriert: %d\n", udpClientCount);
        Serial.printf("Aktuelle Frequenz: %.4f Hz\n", currentFrequency);
        Serial.printf("Freier Heap: %d Bytes\n", ESP.getFreeHeap());
        Serial.println("========================================\n");

        // Wenn keine Clients verbunden sind, erinnere daran
        if (currentClientCount == 0)
        {
          Serial.println("HINWEIS: Keine Clients verbunden!");
          Serial.printf("  - SSID: %s\n", WIFI_AP_SSID);
          Serial.printf("  - Passwort: %s\n", WIFI_AP_PASSWORD);
          Serial.printf("  - IP: %s\n\n", WiFi.softAPIP().toString().c_str());
        }
      }
    }
  }

  // ========== Sensordaten lesen ==========
  sensors_event_t accelerationEvent, gyroscopeEvent, temperatureEvent;
  lsm6ds33.getEvent(&accelerationEvent, &gyroscopeEvent, &temperatureEvent);

  // ========== Hall-Sensor Interrupt-Daten verarbeiten ==========
  // Drain the queue completely; the latest period wins.
  uint32_t interruptTimeDelta;
  while (xQueueReceive(interruptQueue, &interruptTimeDelta, 0) == pdTRUE)
  {
    if (!firstPulseDiscarded)
    {
      // The first period is measured from setup(), not from a previous pulse: ignore it
      firstPulseDiscarded = true;
      continue;
    }

    if (interruptTimeDelta > 0)
    {
      currentFrequency = 1000000.0f / (float)interruptTimeDelta;
      lastPulsePeriodUs = interruptTimeDelta;
      lastPulseMs = millis();
      pulseSeen = true;
    }
  }

  // ========== Pulse-Timeout ==========
  // Report 0 Hz only if no pulse arrived for max(2 s, 3 x last period); a steady rotation keeps its value.
  if (pulseSeen && currentFrequency > 0.0f)
  {
    uint64_t timeoutMs = ((uint64_t)lastPulsePeriodUs * PULSE_TIMEOUT_PERIODS) / 1000ULL;
    if (timeoutMs < PULSE_TIMEOUT_MIN_MS)
    {
      timeoutMs = PULSE_TIMEOUT_MIN_MS;
    }

    if ((uint64_t)(uint32_t)(millis() - lastPulseMs) > timeoutMs)
    {
      if (isDebugMode)
      {
        Serial.printf("DEBUG: No Hall pulse for %lu ms - frequency set to 0\n",
                      (unsigned long)(uint32_t)(millis() - lastPulseMs));
      }
      currentFrequency = 0.0f;
    }
  }

  // ========== Datenpaket formatieren ==========
  // Format: Zeitstempel,Frequenz,Accel_X,Accel_Y,Accel_Z,Gyro_X,Gyro_Y,Gyro_Z,Sequenz
  snprintf(outputBuffer, sizeof(outputBuffer),
           "%lu,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%lu",
           (unsigned long)millis(),
           currentFrequency,
           accelerationEvent.acceleration.x,
           accelerationEvent.acceleration.y,
           accelerationEvent.acceleration.z,
           gyroscopeEvent.gyro.x,
           gyroscopeEvent.gyro.y,
           gyroscopeEvent.gyro.z,
           (unsigned long)sequenceNumber);
  sequenceNumber++; // one sequence number per generated data line; wraps naturally

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
      // Unicast to every live client at its registered ip:port
      for (int i = 0; i < udpClientCount; i++)
      {
        udpSocket.beginPacket(udpClients[i].ip, udpClients[i].port);
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
