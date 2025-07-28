Read the Docs Setup für HRNGGUI
===============================

Dieses Verzeichnis enthält alle notwendigen Dateien für die Verwendung von Read the Docs mit dem HRNGGUI-Projekt.

Erstellte Dateien
-----------------

1. ``.readthedocs.yaml``
~~~~~~~~~~~~~~~~~~~~~~

Die Hauptkonfigurationsdatei für Read the Docs. Sie definiert:

* Python-Version (3.11)
* Build-Umgebung (Ubuntu 22.04)
* Sphinx-Konfiguration
* Abhängigkeiten
* Ausgabeformate (HTML, PDF, EPUB)

2. ``docs/conf.py``
~~~~~~~~~~~~~~~~~

Die Sphinx-Konfigurationsdatei mit folgenden Features:

* Deutscher Sprachsupport
* Read the Docs Theme
* MyST Parser für Markdown-Unterstützung
* Autodoc für automatische API-Dokumentation
* Napoleon für Google/NumPy-Style Docstrings
* Intersphinx für externe Referenzen

3. ``docs/requirements.txt``
~~~~~~~~~~~~~~~~~~~~~~~~~~

Spezifische Abhängigkeiten für die Dokumentationserstellung:

* Sphinx und Extensions
* MyST Parser
* Read the Docs Theme

4. ``docs/index.rst``
~~~~~~~~~~~~~~~~~~

Die Hauptseite der Dokumentation mit:

* Projektübersicht
* Inhaltsverzeichnis mit Toctree
* Schnellstart-Anleitung
* Kontaktinformationen

5. ``setup_readthedocs.py``
~~~~~~~~~~~~~~~~~~~~~~~~~

Ein Python-Skript zur Automatisierung des Setups und Builds:

* Abhängigkeiten installieren
* Dokumentation lokal bauen
* Konfiguration prüfen

Verwendung
----------

Lokale Dokumentation erstellen
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

Vollständiges Setup (empfohlen für ersten Durchlauf)
====================================================
python setup_readthedocs.py

Nur Abhängigkeiten installieren
===============================
python setup_readthedocs.py install

Nur Dokumentation bauen
=======================
python setup_readthedocs.py build

Nur Konfiguration prüfen
========================
python setup_readthedocs.py check


Read the Docs Integration
~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Repository mit Read the Docs verbinden**:

   - Gehen Sie zu https://readthedocs.org
   - Melden Sie sich mit Ihrem GitHub-Account an
   - Klicken Sie auf "Import a Project"
   - Wählen Sie Ihr HRNGGUI-Repository aus

2. **Projekt konfigurieren**:

   - Read the Docs erkennt automatisch die ``.readthedocs.yaml``
   - Die Dokumentation wird bei jedem Push automatisch aktualisiert

3. **Webhook (optional)**:
   - Read the Docs erstellt automatisch einen Webhook in Ihrem Repository
   - Dokumentation wird bei jedem Push neu gebaut

Dokumentationsstruktur
----------------------

Die Dokumentation nutzt Ihre bestehende Markdown-Struktur:

.. code-block:: 

docs/
├── conf.py                 # Sphinx-Konfiguration
├── requirements.txt        # Sphinx-Abhängigkeiten
├── index.rst              # Hauptseite
├── installation.rst       # Installation
├── quickstart.rst         # Schnellstart
├── user-interface.rst     # Benutzeroberfläche
├── configuration.rst      # Konfiguration
├── api/                   # API-Dokumentation
│   └── README.rst
├── development/           # Entwicklerdokumentation
│   └── README.rst
└── _build/               # Build-Ausgabe (automatisch erstellt)
    └── html/
        └── index.html


Features
--------

* **Automatische API-Dokumentation**: Sphinx kann automatisch Docstrings aus Ihrem Python-Code extrahieren
* **Markdown-Unterstützung**: Ihre bestehenden Markdown-Dateien werden unterstützt
* **Mehrere Ausgabeformate**: HTML, PDF, EPUB
* **Suchfunktion**: Integrierte Volltextsuche
* **Responsive Design**: Optimiert für Desktop und Mobile
* **Versionsverwaltung**: Automatische Versionierung basierend auf Git-Tags

Customization
-------------

Theme anpassen
~~~~~~~~~~~~~~

In ``docs/conf.py`` können Sie das Theme und dessen Optionen anpassen:

.. code-block:: python

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}


Erweiterte Konfiguration
~~~~~~~~~~~~~~~~~~~~~~~~

Weitere Sphinx-Extensions können in ``docs/conf.py`` hinzugefügt werden:

.. code-block:: python

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.mathjax',
    'sphinx_copybutton',      # Kopier-Button für Code
    'sphinx_tabs',            # Tab-Interface
    'sphinx_design',          # Design-Komponenten
]


Troubleshooting
---------------

Häufige Probleme
~~~~~~~~~~~~~~~~

1. **Import-Fehler**: Stellen Sie sicher, dass alle Abhängigkeiten installiert sind
2. **Build-Fehler**: Prüfen Sie die Ausgabe des Build-Logs auf Read the Docs
3. **Markdown-Probleme**: MyST Parser unterstützt erweiterte Markdown-Syntax

Logs prüfen
~~~~~~~~~~~

.. code-block:: bash

Lokale Build-Logs anzeigen
==========================
sphinx-build -b html docs docs/_build/html -v


Nützliche Links
---------------

* `Read the Docs Dokumentation <https://docs.readthedocs.io/>`_
* `Sphinx Dokumentation <https://www.sphinx-doc.org/>`_
* `MyST Parser <https://myst-parser.readthedocs.io/>`_
* `Sphinx RTD Theme <https://sphinx-rtd-theme.readthedocs.io/>`_
