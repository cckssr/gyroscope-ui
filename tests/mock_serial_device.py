import os
import pty
import tty
import select
import time
import sys
import random
import argparse
from typing import Optional, Dict, Union
from tempfile import gettempdir

# Füge das übergeordnete Verzeichnis zum Python-Pfad hinzu, um src zu finden
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.debug_utils import Debug


class MockGMCounter:
    """
    Eine Mock-Klasse für GMCounter, die dessen Verhalten für Testzwecke simuliert,
    ohne ein physisches Gerät zu benötigen.
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        timeout: float = 1.0,
        max_tick: float = 1.0,
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.max_tick = max_tick
        self._min_tick = 0.000_08  # Minimal tick (80 us)
        self._voltage = 500
        self._repeat = False
        self._counting = False
        self._counting_time_mode = 2
        self._count = 0
        self._last_count = 0
        self._measurement_start_time = 0.0
        self._last_pulse_time = 0.0
        self.next_pulse_time = 0
        self._next_pulse_interval = 0.0  # Das nächste zufällige Intervall
        Debug.info(f"MockGMCounter für Port {port} initialisiert")
        print(
            f"Baudrate: {self.baudrate}, timeout: {self.timeout:2f}, max_tick: {self.max_tick:6f}"
        )

    def get_data(self) -> Optional[Dict[str, Union[int, bool]]]:
        counting_time_map = {0: 0, 1: 1, 2: 10, 3: 60, 4: 100, 5: 300}
        ct = counting_time_map.get(self._counting_time_mode, 0)

        progress = 0
        if self._counting and ct > 0:
            elapsed = time.time() - self._measurement_start_time
            progress = min(100, int((elapsed / ct) * 100))

        data = {
            "count": self._count,
            "last_count": self._last_count,
            "counting_time": ct,
            "repeat": self._repeat,
            "progress": progress,
            "voltage": self._voltage,
        }
        return data if data["voltage"] != 0 else None

    def read_time_fast(self) -> Optional[int]:
        if not self._counting:
            return None
        current_time = time.time()
        if self._last_pulse_time == 0.0:
            self._last_pulse_time = current_time
            return None
        delta_micros = (current_time - self._last_pulse_time) * 1_000_000
        self._last_pulse_time = current_time
        print(current_time)
        return int(delta_micros)

    def get_information(self) -> Dict[str, str]:
        return {"copyright": "(C) Mock-Gerät", "version": "MockVersion 1.0.0"}

    def set_voltage(self, value: int = 500):
        if 300 <= value <= 700:
            self._voltage = value
            Debug.info(f"MockGMCounter: Spannung auf {self._voltage}V gesetzt.")

    def set_repeat(self, value: bool = False):
        self._repeat = value
        Debug.info(f"MockGMCounter: Wiederholungsmodus auf {self._repeat} gesetzt.")

    def set_counting(self, value: bool = False):
        if value and not self._counting:  # Start counting
            self._counting = True
            self._last_count = self._count
            self._count = 0
            self._measurement_start_time = time.time()

            # Generiere das erste zufällige Intervall
            self._next_pulse_interval = random.uniform(self._min_tick, self.max_tick)
            self.next_pulse_time = time.time() + self._next_pulse_interval

            Debug.info(
                f"MockGMCounter: Zählung gestartet. Erstes Intervall: {self._next_pulse_interval:.6f}s"
            )
        elif not value and self._counting:  # Stop counting
            self._counting = False
            Debug.info(f"MockGMCounter: Zählung gestoppt. Finaler Count: {self._count}")

    def set_speaker(self, gm: bool = False, ready: bool = False):
        Debug.info(f"MockGMCounter: Lautsprecher auf gm={gm}, ready={ready} gesetzt.")

    def set_counting_time(self, value: int = 0):
        if 0 <= value <= 5:
            self._counting_time_mode = value
            Debug.info(f"MockGMCounter: Zählzeit-Modus auf {value} gesetzt.")

    def handle_command(self, command: str) -> Optional[str]:
        """Verarbeitet einen Befehl und gibt eine Antwortzeichenfolge zurück."""
        # Während der Zählung nur 's0' (Stopp) erlauben
        if self._counting and command != "s0":
            return None

        response = None
        if command == "b2":
            data_dict = self.get_data()
            if data_dict:
                response = (
                    f"{data_dict['count']},"
                    f"{data_dict['last_count']},"
                    f"{data_dict['counting_time']},"
                    f"{int(data_dict['repeat'])},"
                    f"{data_dict['progress']},"
                    f"{data_dict['voltage']},"
                )
        elif command == "c":
            response = self.get_information()["copyright"]
        elif command == "v":
            response = self.get_information()["version"]
        elif command.startswith("j"):
            self.set_voltage(int(command[1:]))
        elif command.startswith("o"):
            self.set_repeat(bool(int(command[1:])))
        elif command.startswith("s"):
            is_counting = bool(int(command[1:]))
            self.set_counting(is_counting)
        elif command.startswith("U"):
            val = int(command[1:])
            self.set_speaker(gm=bool(val & 1), ready=bool(val & 2))
        elif command.startswith("f"):
            self.set_counting_time(int(command[1:]))
        return response

    def tick(self) -> Optional[int]:
        """Wird periodisch aufgerufen, um spontane Daten zu erzeugen."""
        if not self._counting:
            return None

        # Prüfen, ob die Zählzeit abgelaufen ist
        counting_time_map = {0: 0, 1: 1, 2: 10, 3: 60, 4: 100, 5: 300}
        time_limit = counting_time_map.get(self._counting_time_mode, 0)
        if time_limit > 0:
            elapsed_time = time.time() - self._measurement_start_time
            if elapsed_time >= time_limit:
                self.set_counting(False)
                return None  # Messung ist beendet, keine weiteren Pulse senden

        # Nächsten Impuls erzeugen
        if time.time() >= self.next_pulse_time:
            current_time = time.time()

            # Verwende das vorgenerierte Intervall für diesen Puls
            current_interval_us = int(self._next_pulse_interval * 1_000_000)

            self._count += 1  # Zähler bei einem Impuls erhöhen

            # Generiere das nächste zufällige Intervall
            self._next_pulse_interval = random.uniform(self._min_tick, self.max_tick)
            self.next_pulse_time = current_time + self._next_pulse_interval

            Debug.debug(
                f"Mock Pulse! Count: {self._count}, Time: {current_interval_us} us, Next in: {self._next_pulse_interval:.6f}s"
            )
            return str(current_interval_us)
        return None


def main(device_class=MockGMCounter):
    """
    Erstellt eine virtuelle serielle Schnittstelle und simuliert ein Gerät.
    """
    port_file = os.path.join(gettempdir(), "virtual_serial_port.txt")

    master, slave = pty.openpty()
    slave_name = os.ttyname(slave)
    print(f"Virtueller serieller Port erstellt: {slave_name}")

    # Schreibe den Port-Namen in eine Datei, damit andere Prozesse ihn lesen können
    try:
        with open(port_file, "w", encoding="utf-8") as f:
            f.write(slave_name)
        print(f"Port-Name wurde in '{port_file}' geschrieben.")
    except IOError as e:
        print(f"Fehler beim Schreiben der Port-Datei: {e}")

    print("Sie können sich mit Ihrer Anwendung mit diesem Port verbinden.")
    print("Drücken Sie Strg+C zum Beenden.")

    tty.setraw(master)

    mock_device = device_class(port=slave_name)

    try:
        while True:
            r, _, _ = select.select([master], [], [], 0.1)

            if r:
                try:
                    data = os.read(master, 1024).decode(errors="ignore").strip()
                    if not data:
                        print("Verbindung geschlossen.")
                        break

                    print(f"Empfangen: {data}")
                    response = mock_device.handle_command(data)

                    if response:
                        os.write(master, (response + "\n").encode("utf-8"))

                except (OSError, ValueError) as e:
                    print(f"Fehler: {e}")
                    break

            # Spontane Daten vom Gerät verarbeiten
            spontaneous_data = mock_device.tick()
            if spontaneous_data:
                os.write(
                    master,
                    bytes([0xAA]) + spontaneous_data.to_bytes(4, byteorder="big"),
                )

    except KeyboardInterrupt:
        print("\nProgramm wird beendet...")
    finally:
        os.close(master)
        os.close(slave)
        print("Virtueller serieller Port geschlossen.")
        # Räume die Port-Datei auf
        if os.path.exists(port_file):
            try:
                os.remove(port_file)
                print(f"Port-Datei '{port_file}' wurde entfernt.")
            except OSError as e:
                print(f"Fehler beim Entfernen der Port-Datei: {e}")


if __name__ == "__main__":
    # Hier könnte man z.B. über Kommandozeilenargumente eine andere Geräteklasse auswählen.
    # z.B. main(device_class=MyOtherMockDevice)
    parser = argparse.ArgumentParser(description="Starte das Mock-Serial-Gerät.")
    parser.add_argument(
        "--baudrate", type=int, default=9600, help="Baudrate für das Mock-Gerät"
    )
    parser.add_argument(
        "--timeout", type=float, default=1.0, help="Timeout für das Mock-Gerät"
    )
    parser.add_argument(
        "--max-tick",
        type=float,
        default=1.0,
        help="Maximale Zeit zwischen Impulsen (Sekunden)",
    )
    args = parser.parse_args()

    def device_factory(port):
        return MockGMCounter(
            port=port,
            baudrate=args.baudrate,
            timeout=args.timeout,
            max_tick=args.max_tick,
        )

    main(device_class=device_factory)
