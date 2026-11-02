"""Structure of the main window form (the logic comes with the main window class)."""

from __future__ import annotations

import pytest
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDockWidget,
    QMainWindow,
    QMenu,
    QMenuBar,
    QScrollArea,
    QSpacerItem,
    QStatusBar,
    QTabWidget,
    QToolBar,
)

from gyroscope_ui.infrastructure.config import load_config
from gyroscope_ui.pyqt.preview import build_form

TEXTS = load_config().section("ui")["main_window"]


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
    assert dock.windowTitle() == TEXTS["dockControls@title"]
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
    assert window.windowTitle() == TEXTS["self@title"]


def test_actions_menus_and_toolbar(window):
    actions = {a.objectName(): a for a in window.findChildren(QAction) if a.objectName()}
    names = (
        "actionConnect",
        "actionStartStop",
        "actionSave",
        "actionShortcuts",
        "actionOpenDataFolder",
        "actionQuit",
        "actionAbout",
    )
    for name in names:
        assert actions[name].text() == TEXTS[name]
        assert actions[name].toolTip() == TEXTS[f"{name}@tooltip"]
        assert actions[name].shortcut().isEmpty(), f"{name}: keys belong to config.json"
    # no menu bar: it takes space on small screens, everything is in the toolbar
    assert window.findChild(QMenuBar) is None and window.findChild(QMenu) is None
    toolbar = window.findChild(QToolBar, "toolBar")
    assert [a.objectName() if a.objectName() else "-" for a in toolbar.actions()] == [
        "actionConnect",
        "-",
        "actionStartStop",
        "actionSave",
        "actionOpenDataFolder",
        "-",
        "actionShortcuts",
        "actionAbout",
        "-",
        "actionQuit",
    ]
