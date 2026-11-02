# Tastenkürzel

Die Tastenkürzel gelten im ganzen Fenster, auch wenn gerade ein Eingabefeld (z. B. die Untergruppe) den Fokus hat. Sie werden von einem einzigen Event-Filter der Anwendung verarbeitet und stehen in `gyroscope_ui/config.json` unter `shortcuts`. Diese Datei wird erzeugt (`python -m gyroscope_ui.ui.shortcuts > docs/SHORTCUTS.md`).

## Messung

| Funktion                  | macOS | Windows/Linux |
| ------------------------- | ----- | ------------- |
| Messung starten / stoppen | `␣`   | `Space`       |
| Messung stoppen           | `⎋`   | `Esc`         |
| Messung zurücksetzen      | `⌘R`  | `Ctrl+R`      |

## Speichern

| Funktion          | macOS | Windows/Linux |
| ----------------- | ----- | ------------- |
| Messung speichern | `⌘S`  | `Ctrl+S`      |

## Gerät

| Funktion            | macOS | Windows/Linux |
| ------------------- | ----- | ------------- |
| Verbinden / Trennen | `⌘K`  | `Ctrl+K`      |

## Diagramme

| Funktion                 | macOS | Windows/Linux  |
| ------------------------ | ----- | -------------- |
| Auto-Range der Diagramme | `⇧⌘A` | `Ctrl+Shift+A` |

## Fenster

| Funktion                 | macOS | Windows/Linux |
| ------------------------ | ----- | ------------- |
| Zu Reiter n wechseln     | `⌘1`  | `Ctrl+1`      |
| Diese Übersicht anzeigen | `F1`  | `F1`          |

Hinweise: Die Leertaste wirkt nicht, solange eine Schaltfläche oder ein Textfeld den Fokus hat (dort klickt bzw. schreibt sie). Auf macOS ist `Ctrl` die Befehlstaste (⌘), `Alt` die Wahltaste (⌥); die Kürzel lassen sich in `config.json` umbelegen.
