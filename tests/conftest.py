from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Safe fallback for iCloud Drive duplication files which cause pytest import/collection crash
collect_ignore_glob = ["* 2.py"]
