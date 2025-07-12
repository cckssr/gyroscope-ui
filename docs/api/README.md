# API-Dokumentation

Die automatisch generierte API-Dokumentation basiert auf den Docstrings im Python-Code.

## Hauptmodule

```{toctree}
:maxdepth: 2

main-window
data-controller
plot-widget
helper-classes
debug-utils
arduino-gmcounter
```

## Automatisch generierte Dokumentation

### src.main_window

```{automodule} src.main_window
:members:
:undoc-members:
:show-inheritance:
```

### src.data_controller

```{automodule} src.data_controller
:members:
:undoc-members:
:show-inheritance:
```

### src.device_manager

```{automodule} src.device_manager
:members:
:undoc-members:
:show-inheritance:
```

### src.control

```{automodule} src.control
:members:
:undoc-members:
:show-inheritance:
```

### src.plot

```{automodule} src.plot
:members:
:undoc-members:
:show-inheritance:
```

### src.helper_classes

```{automodule} src.helper_classes
:members:
:undoc-members:
:show-inheritance:
```

### src.debug_utils

```{automodule} src.debug_utils
:members:
:undoc-members:
:show-inheritance:
```

## Verwendung

Die API-Dokumentation wird automatisch aus den Docstrings im Code generiert. Stellen Sie sicher, dass Ihre Funktionen und Klassen ordnungsgemäß dokumentiert sind:

```python
class MainWindow(QMainWindow):
    """Main window of the HRNGGUI application.

    It handles the user interface, the device connection and the
    processing of the recorded data.  The implementation is split
    into several functional sections:

    1. Initialization and setup
    2. Data processing and statistics
    3. Measurement management
    4. UI event handlers
    5. Device control
    6. Helper functions
    """

    def __init__(self, device_manager: DeviceManager, parent=None):
        """
        Initialisiert das Hauptfenster und alle Komponenten der Anwendung.

        Args:
            device_manager (DeviceManager): Der verbundene Geräte-Manager
            parent: Das übergeordnete Widget (optional)
        """
        # Implementation...
```

## Docstring-Stile

Die Dokumentation unterstützt sowohl Google- als auch NumPy-Style Docstrings:

### Google Style

```python
def function_with_types_in_docstring(param1, param2):
    """Example function with types documented in the docstring.

    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    Returns:
        bool: The return value. True for success, False otherwise.
    """
    return True
```

### NumPy Style

```python
def function_with_numpy_docstring(param1, param2):
    """Example function with NumPy style docstring.

    Parameters
    ----------
    param1 : int
        The first parameter.
    param2 : str
        The second parameter.

    Returns
    -------
    bool
        The return value. True for success, False otherwise.
    """
    return True
```
