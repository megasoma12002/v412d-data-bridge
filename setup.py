#!/usr/bin/env python3
"""Discover flat ``scripts/*.py`` as top-level importable modules.

Keeps historical ``from live_config import LIVE`` import style while making
``pip install -e .`` the supported way to put modules on ``sys.path``.
Do not add ``sys.path.insert`` shims in scripts or tests.
"""
from __future__ import annotations

from pathlib import Path

from setuptools import setup

SCRIPTS = Path(__file__).resolve().parent / "scripts"
PY_MODULES = sorted(
    p.stem
    for p in SCRIPTS.glob("*.py")
    if p.is_file() and p.stem != "__init__" and not p.stem.startswith(".")
)

setup(
    package_dir={"": "scripts"},
    py_modules=PY_MODULES,
)
