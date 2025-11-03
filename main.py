#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Robust launcher for the application. When executed as a script from the
repository root or from an installed package folder the module `src.main`
should be executed as a module so that its intra-package relative imports work
correctly. On Windows executing a script inside a package folder often fails
with "attempted relative import with no known parent" if the module is simply
imported; to avoid this we prefer runpy.run_module and fall back to sensible
import attempts.

This file is intentionally small and defensive so users can run the repository
entrypoint (``python main.py``) or the installed entrypoint that points here.
"""

from __future__ import annotations
import runpy
import sys
from importlib import import_module


def _run_module_by_name(module_names: list[str]) -> None:
    """Try to run one of the given module names as __main__.

    The list is tried in order; the function raises the last exception if
    none succeeded.
    """
    last_exc: Exception | None = None
    for mod in module_names:
        try:
            # run_module executes the module in the module context, so
            # relative imports inside the module work as expected.
            runpy.run_module(mod, run_name="__main__", alter_sys=True)
            return
        except ModuleNotFoundError as exc:
            last_exc = exc
        except Exception as exc:  # pragma: no cover - surface other errors
            last_exc = exc
    if last_exc:
        raise last_exc


def _import_and_call_main(module_names: list[str]) -> None:
    """Fallback: import module and call its `main()` function if present."""
    last_exc: Exception | None = None
    for mod in module_names:
        try:
            m = import_module(mod)
            if hasattr(m, "main") and callable(getattr(m, "main")):
                m.main()
                return
        except Exception as exc:
            last_exc = exc
    if last_exc:
        raise last_exc


if __name__ == "__main__":
    # Typical names we try: local package `src` (repo layout) and installed
    # package `gyroscope_ui` (distribution layout). Try running the module
    # first (preserves package context), fall back to import+call.
    module_candidates = ["src.main", "gyroscope_ui.main"]

    try:
        _run_module_by_name(module_candidates)
    except Exception:
        # Last resort: try import and call main()
        try:
            _import_and_call_main(module_candidates)
        except Exception as exc:  # pragma: no cover - report to user
            print(
                "Failed to start application; attempted modules:",
                module_candidates,
                file=sys.stderr,
            )
            raise
