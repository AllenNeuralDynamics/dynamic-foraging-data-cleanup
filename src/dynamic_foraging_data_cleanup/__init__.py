"""Declares some useful package_level metadata"""

import importlib.metadata
from pathlib import Path
import sys

from platformdirs import site_data_dir

__version__ = importlib.metadata.version(__package__)

APP_NAME = __package__
ORGANIZATION = "AllenInstitute"

# On windows, DATA_DIR resolves to C:\ProgramData\{ORGANIZATION}\{APP_NAME}
DATA_DIR = Path(
    site_data_dir(
        APP_NAME,
        appauthor=ORGANIZATION,
        ensure_exists=True,
    )
)

PYTHON_VERSION = sys.version
PYTHON_EXE = sys.executable
PACKAGES = {d.metadata["name"]: d.version for d in importlib.metadata.distributions()}
