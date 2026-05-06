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
#define SECRET_PASS "BosonBoson"

/** @brief Router SSID für OTA-Updates */
#define SECRET_STA_SSID "YourRouterSSID"

/** @brief Router Passwort für OTA-Updates */
#define SECRET_STA_PASS "YourRouterPassword"

#endif // SECRETS_H
