"""Structure of the main window form (the logic comes with the main window class)."""

from __future__ import annotations

import pytest
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDockWidget,
    QMainWindow,
    QMenu,
    QScrollArea,
    QSpacerItem,
    QStatusBar,
    QTabWidget,
    QToolBar,
)

from gyroscope_ui.pyqt.preview import build_form


@pytest.fixture
def window(qtbot) -> QMainWindow:
    widget = build_form("main_window")
    qtbot.addWidget(widget)
    widget.show()
    return widget


def test_structure(window):
    assert isinstance(window.centralWidget(), QTabWidget)
    assert window.centralWidget().objectName() == "tabs"
    dock = window.findChild(QDockWidget, "dockControls")
    assert dock.windowTitle() == "Steuerung"
    assert dock.features() == (
        QDockWidget.DockWidgetFeature.DockWidgetMovable
        | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        | QDockWidget.DockWidgetFeature.DockWidgetClosable
    )
    scroll = window.findChild(QScrollArea, "scrollControls")
    assert scroll.widgetResizable()
    assert scroll.widget().objectName() == "controlsContent"
    layout = scroll.widget().layout()
    assert layout.objectName() == "layoutControls"
    assert layout.count() == 1 and isinstance(layout.itemAt(0), QSpacerItem)
    assert isinstance(window.findChild(QStatusBar, "statusBar"), QStatusBar)
    assert window.windowTitle() == "Kreisel-GUI"


def test_actions_menus_and_toolbar(window):
    actions = {a.objectName(): a for a in window.findChildren(QAction) if a.objectName()}
    expected = {
        "actionConnect": "Verbinden",
        "actionStartStop": "Start",
        "actionSave": "Speichern …",
        "actionShortcuts": "Tastenkürzel",
        "actionOpenDataFolder": "Datenordner öffnen",
        "actionQuit": "Beenden",
    }
    for name, text in expected.items():
        assert actions[name].text() == text
        assert actions[name].toolTip()
        assert actions[name].shortcut().isEmpty(), f"{name}: keys belong to config.json"
    assert "actionAbout" in actions
    toolbar = window.findChild(QToolBar, "toolBar")
    assert [a.objectName() for a in toolbar.actions() if a.objectName()] == [
        "actionConnect",
        "actionStartStop",
        "actionSave",
        "actionShortcuts",
    ]
    file_menu = window.findChild(QMenu, "menuFile")
    assert file_menu.title() == "Datei"
    assert [a.objectName() for a in file_menu.actions() if not a.isSeparator()] == [
        "actionSave",
        "actionOpenDataFolder",
        "actionQuit",
    ]
    help_menu = window.findChild(QMenu, "menuHelp")
    assert help_menu.title() == "Hilfe"
    assert [a.objectName() for a in help_menu.actions()] == ["actionShortcuts", "actionAbout"]
