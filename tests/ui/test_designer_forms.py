"""Every Designer form builds on its own (no controllers, devices or data) and shows."""

from __future__ import annotations

import pytest

from gyroscope_ui.pyqt.preview import build_form
from gyroscope_ui.pyqt.sync_texts import PYQT_DIR

FORMS = sorted(path.stem for path in PYQT_DIR.glob("*.ui"))


@pytest.mark.parametrize("form", FORMS)
def test_form_opens_without_logic(qtbot, form: str) -> None:
    widget = build_form(form)
    qtbot.addWidget(widget)
    widget.show()
    assert widget.isVisible()
