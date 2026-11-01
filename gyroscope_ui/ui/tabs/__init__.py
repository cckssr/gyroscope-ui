"""Central tabs. Importing this package registers the built-in tabs."""

from gyroscope_ui.ui.tabs.registry import TabBase, TabRegistry

# Tab modules are imported here once they exist (each registers itself), e.g.:
#   from gyroscope_ui.ui.tabs import measurement_tab  # noqa: F401

__all__ = ["TabBase", "TabRegistry"]
