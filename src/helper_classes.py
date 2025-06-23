import re
import json
from datetime import datetime

try:  # pragma: no cover - allow usage without Qt installation
    from PySide6.QtWidgets import (
        QStatusBar,
        QLabel,
        QMessageBox,
        QDialog,
        QWidget,
        QDialogButtonBox,
        QFileDialog,
    )
    from PySide6.QtCore import QTimer
except Exception:  # Fallback stubs for headless testing

    class QStatusBar:  # pragma: no cover - stub
        def __init__(self):
            pass

        def setStyleSheet(self, *args, **kwargs):
            pass

        def showMessage(self, *args, **kwargs):
            pass

        def insertPermanentWidget(self, *args, **kwargs):
            pass

        def currentMessage(self):
            return ""

        def styleSheet(self):
            return ""

    class QLabel:
        def setText(self, *args, **kwargs):
            pass

    class QMessageBox:
        Critical = None

    class QDialog:
        pass

    class QWidget:
        pass

    class QDialogButtonBox:
        def addButton(self, *args, **kwargs):
            class _B:
                def clicked(self):
                    pass

                def connect(self, *a, **k):
                    pass

            return _B()

    class QFileDialog:
        pass

    class QTimer:
        @staticmethod
        def singleShot(*args, **kwargs):
            pass


from pyqt.ui_alert import Ui_Dialog
from src.debug_utils import Debug


class Statusbar:
    """
    A class to manage the status bar messages and styles.
    Attributes:
        statusbar (QStatusBar): The status bar widget.
        old_state (list): The previous state of the status bar.
    Methods:
        __init__(statusbar: QStatusBar):
            Initializes the Statusbar with the given QStatusBar widget.
        temp_message(message: str, backcolor: str = None, duration: int = None):
            Displays a temporary message on the status bar.
        perm_message(message: str, index: int = 0, backcolor: str = None):
            Displays a permanent message on the status bar.
        _update_statusbar_style(backcolor: str):
            Updates the style of the status bar.
        _save_state():
            Saves the current state of the status bar.
    """

    def __init__(self, statusbar: QStatusBar) -> None:
        self.statusbar = statusbar
        self.old_state: list[str] = []
        self._save_state()

    def temp_message(
        self, message: str, backcolor: str = "", duration: int = 0
    ) -> None:
        new_style = self._update_statusbar_style(backcolor)
        # set statusbar style
        self.statusbar.setStyleSheet(new_style)

        # Set new message and if duration is provided, reset after the duration elapses
        if duration:
            self.statusbar.showMessage(message, duration)
            Debug.info(f"Statusbar message: {message} with duration: {duration}")
            # reset to old state after duration
            QTimer.singleShot(
                duration, lambda: self.statusbar.setStyleSheet(self.old_state[1])
            )
            QTimer.singleShot(
                duration, lambda: self.statusbar.showMessage(self.old_state[0])
            )
        else:
            self.statusbar.showMessage(message)
            Debug.info(f"Permanent Statusbar message: {message}")

    def perm_message(self, message: str, index: int = 0, backcolor: str = "") -> None:
        new_style = self._update_statusbar_style(backcolor)
        self.statusbar.setStyleSheet(new_style)
        label = QLabel()
        label.setText(message)
        self.statusbar.insertPermanentWidget(index, label)
        Debug.info(f"Permanent Statusbar message: {message} at index: {index}")

    def _update_statusbar_style(self, backcolor: str) -> str:
        # get current state
        self._save_state()

        # Set new style if backcolor is provided or keep the old style
        if backcolor:
            if "background-color:" in self.old_state[1]:
                # if old style had backcolor, replace it with the new one
                new_style = self.old_state[1].replace(
                    re.search(r"background-color:\s*[^;]+;", self.old_state[1]).group(
                        0
                    ),
                    f"background-color: {backcolor};",
                )
                Debug.info(
                    f"Statusbar background color updated: {self.old_state[1]} -> {new_style}"
                )
            else:
                # otherwise append the new backcolor
                new_style = self.old_state[1] + f"background-color: {backcolor};"
                Debug.info(f"Statusbar background color set: {new_style}")
        else:
            new_style = self.old_state[1]
            Debug.info("No background color change")
        return new_style

    def _save_state(self):
        self.old_state = [self.statusbar.currentMessage(), self.statusbar.styleSheet()]


class AlertWindow(QDialog):
    """
    Initializes the alert window with customizable buttons and messages.
    Provides tracking for which button was clicked.
    """

    def __init__(
        self,
        parent: QWidget,
        message: str = "Alert",
        title: str = "Warning",
        buttons=None,
    ) -> None:
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(title)

        # Speichert den zuletzt geklickten Button
        self.clicked_button = None
        self.clicked_role = None
        self.clicked_text = None

        # Set message im TextBox-Label
        if hasattr(self.ui, "textBox"):
            self.ui.textBox.setText(message)

        # Configure buttons if provided
        if buttons and hasattr(self.ui, "buttonBox"):
            # Bestehende Signalverbindungen sichern
            old_accepted = None
            old_rejected = None

            if hasattr(self.ui.buttonBox, "accepted") and hasattr(
                self.ui.buttonBox.accepted, "connect"
            ):
                old_accepted = self.ui.buttonBox.accepted
                try:
                    self.ui.buttonBox.accepted.disconnect()
                except:
                    pass

            if hasattr(self.ui.buttonBox, "rejected") and hasattr(
                self.ui.buttonBox.rejected, "connect"
            ):
                old_rejected = self.ui.buttonBox.rejected
                try:
                    self.ui.buttonBox.rejected.disconnect()
                except:
                    pass

            # Bestehende Buttons löschen
            self.ui.buttonBox.clear()

            # Neue Buttons hinzufügen und mit Callbacks verbinden
            for button_text, role in buttons:
                button = self.ui.buttonBox.addButton(button_text, role)
                # Button-Klick-Handler hinzufügen
                button.clicked.connect(
                    lambda checked=False, b=button, r=role, t=button_text: self._handle_button_clicked(
                        b, r, t
                    )
                )

            # Allgemeine Dialog-Ereignisse mit unseren Button-Tracking verbinden
            if old_accepted:
                self.ui.buttonBox.accepted.connect(self.accept)
            if old_rejected:
                self.ui.buttonBox.rejected.connect(self.reject)

    def _handle_button_clicked(self, button, role, text):
        """
        Speichert Informationen über den angeklickten Button.
        """
        Debug.info(f"Button geklickt: {text} mit Rolle {role}")
        self.clicked_button = button
        self.clicked_role = role
        self.clicked_text = text

        # Dialog entsprechend der Rolle beenden
        if role == QDialogButtonBox.ButtonRole.AcceptRole:
            self.accept()
        elif role == QDialogButtonBox.ButtonRole.RejectRole:
            self.reject()
        # Bei anderen Rollen (ActionRole, ResetRole, etc.) lassen wir den Dialog offen

    def get_clicked_button(self):
        """
        Gibt den angeklickten Button zurück.

        Returns:
            QPushButton: Der angeklickte Button oder None
        """
        return self.clicked_button

    def get_clicked_role(self):
        """
        Gibt die Rolle des angeklickten Buttons zurück.

        Returns:
            QDialogButtonBox.ButtonRole: Die Rolle des angeklickten Buttons oder None
        """
        return self.clicked_role

    def get_clicked_text(self):
        """
        Gibt den Text des angeklickten Buttons zurück.

        Returns:
            str: Der Text des angeklickten Buttons oder None
        """
        return self.clicked_text


class Helper:
    """
    A helper class with static methods for common tasks.
    Methods:
        close_event(parent, event):
            Handles the close event for a window.
    """

    @staticmethod
    def close_event(parent, event):
        # Debug-Logging hinzufügen
        print("Schließen-Event wurde ausgelöst - frage Benutzer nach Bestätigung")
        reply = QMessageBox.question(
            parent,
            "Beenden",
            "Wollen Sie sicher das Programm schließen?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            print("Benutzer hat bestätigt - Programm wird beendet")
            event.accept()
        else:
            print("Benutzer hat abgebrochen - Programm läuft weiter")
            event.ignore()


class SaveManager:
    """
    A class to handle file saving operations.
    Methods:
        save_file_dialog(parent, file_type: str, file_name: str = ""):
            Opens a file dialog to save a file with the specified type and name.
    """

    def filename_auto(self, rad_sample: str, suffix: str = "") -> str:
        """
        Generates a filename based on the current date and time, with an optional suffix.
        Args:
            rad_sample (str): The sample name to include in the filename.
            suffix (str): An optional suffix to append to the filename.
        Returns:
            str: The generated filename.
        """
        # Check if radioactive sample name is provided
        if not rad_sample:
            Debug.error("Radioactive sample name cannot be empty.")
            return ""

        now = datetime.now()
        timestamp = now.strftime("%Y_%m_%d")

        if suffix and not suffix.startswith("-"):
            suffix = "-" + suffix

        return f"{timestamp}-{rad_sample}{suffix}"


def import_config(language: str = "de") -> dict:
    """
    Imports the language-specific configuration from config.json.
    Args:
        language (str): The language code to load the configuration for (default is "de").
    Returns:
        dict: The configuration dictionary.
    """
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            return config[language]
    except FileNotFoundError:
        Debug.error(
            "config.json not found. Please ensure it exists in the project root."
        )
        return {}
    except json.JSONDecodeError as e:
        Debug.error(f"Error decoding JSON from config.json: {e}")
        return {}
