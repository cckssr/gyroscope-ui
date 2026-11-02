/**
 * @file secrets.h
 * @brief WiFi-Konfigurationsdatei für das Gyroscope Data Acquisition System
 *
 * Diese Datei enthält vertrauliche WiFi-Verbindungsdaten und sollte
 * nicht in der Versionskontrolle gespeichert werden.
 *
 * @warning Passwort muss mindestens 8 Zeichen lang sein
 * @note Diese Datei sollte in .gitignore eingetragen werden
 */

#ifndef SECRETS_H
#define SECRETS_H

/** @brief WiFi-Netzwerk Passwort (mindestens 8 Zeichen) */
#define SECRET_PASS "ChangeMe-WiFi"

/** @brief Router SSID für OTA-Updates */
#define SECRET_STA_SSID "ChangeMe-RouterSSID"

/** @brief Router Passwort für OTA-Updates */
#define SECRET_STA_PASS "ChangeMe-RouterPassword"

/**
 * @brief Optional second router for OTA updates (e.g. another building or a hotspot).
 *        If both are defined, the strongest known network in range is chosen at boot.
 */
// #define SECRET_STA_SSID2 "ChangeMe-RouterSSID2"
// #define SECRET_STA_PASS2 "ChangeMe-RouterPassword2"

/**
 * @brief OTA upload password (ArduinoOTA)
 * @warning Must differ from SECRET_PASS (the WiFi password the students know).
 *          The same value goes into secrets.ini (see secrets.ini.template).
 */
#define SECRET_OTA_PASS "ChangeMe-OTA"

#endif // SECRETS_H
