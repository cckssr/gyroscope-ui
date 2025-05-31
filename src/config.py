"""
Zentrale Konfigurationsdatei für die HRNGGUI-Anwendung.
Stellt Konstanten und Standardwerte für die gesamte Anwendung bereit.
"""

# Anwendungsname
APP_NAME = "hrnggui"

# Debug-Einstellungen
DEBUG_LEVEL_DEFAULT = "verbose"  # 'off', 'basic', 'verbose'

# Plot-Konfiguration
MAX_PLOT_POINTS = 50
PLOT_X_LABEL = "Ereignis k"
PLOT_Y_LABEL = "Zeit / µs"

# Timer-Einstellungen (in Millisekunden)
CONTROL_UPDATE_INTERVAL = 1000  # 1 Sekunde
STATISTICS_UPDATE_INTERVAL = 2000  # 2 Sekunden
ACQUISITION_TIMER_INTERVAL = 100  # 0.1 Sekunden

# DataController-Konfiguration
MAX_HISTORY_SIZE = 100

# Zählwert-Mapping für Anzeigedauer
COUNT_TIME_MAP = {0: 999, 1: 1, 2: 10, 3: 60, 4: 100, 5: 300}

# GM-Counter Einstellungen
DEFAULT_VOLTAGE = 500  # Volt

# UI-Farbschema
COLOR_GREEN = "green"
COLOR_RED = "red"
COLOR_ORANGE = "orange"
COLOR_BLUE = "blue"

# Nachrichtentext
MSG_APP_INIT = "Anwendung wird initialisiert..."
MSG_CONNECTED = "Verbunden mit {}. Bereit für Messungen."
MSG_MEASUREMENT_RUNNING = "Messung läuft..."
MSG_MEASUREMENT_STOPPED = "Messung gestoppt."
MSG_MEASUREMENT_ENDED = (
    "Messung beendet. Bereit zum Speichern oder für eine neue Messung."
)
MSG_SETTINGS_APPLIED = "Einstellungen erfolgreich angewendet."
MSG_DATA_SAVED = "Daten gespeichert in {}"
MSG_NO_DATA = "Es sind keine Messdaten zum Speichern verfügbar."
MSG_UNSAVED_DATA = "Sie haben ungespeicherte Messdaten. Möchten Sie diese verwerfen und eine neue Messung starten?"
MSG_CONNECTION_FAILED = "Verbindung zum Gerät fehlgeschlagen. Anwendung wird beendet."
