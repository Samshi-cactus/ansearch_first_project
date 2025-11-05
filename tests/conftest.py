"""Pytest configuration: path setup + warning filters for clean CI logs."""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

# Ensure project root is on sys.path (so 'src' and 'scripts' import cleanly)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Silence 3rd-party deprecations that we do not control (spaCy/Click).
warnings.filterwarnings(
    "ignore",
    message="Importing 'parser.split_arg_string' is deprecated",
    category=DeprecationWarning,
    module=r"spacy\.cli\._util",
)
warnings.filterwarnings(
    "ignore",
    message="Importing 'parser.split_arg_string' is deprecated",
    category=DeprecationWarning,
    module=r"weasel\.util\.config",
)
