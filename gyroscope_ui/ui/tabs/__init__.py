"""Central tabs. Importing this package registers the built-in tabs."""

# Importing a tab module registers the tab.
from gyroscope_ui.ui.tabs import measurement_tab  # noqa: F401, E402
from gyroscope_ui.ui.tabs.registry import TabBase, TabRegistry

__all__ = ["TabBase", "TabRegistry"]
