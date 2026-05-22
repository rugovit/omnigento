#!/usr/bin/env python3
"""Staged legacy AI instruction normalization CLI."""

from __future__ import annotations

import sys
from pathlib import Path

SEED_ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = SEED_ROOT / "lib"
sys.path.insert(0, str(LIB_DIR))

from normalizer.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
