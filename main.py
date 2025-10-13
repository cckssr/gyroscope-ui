#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Thin shim to run the application from the repository root without duplicating
the actual entrypoint logic. The canonical entrypoint is `src/main.py` (package
module `gyroscope_ui.main:main`).
"""

from src.main import main

if __name__ == "__main__":
    main()
