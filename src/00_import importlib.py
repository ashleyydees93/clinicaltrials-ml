mport importlib
import subprocess
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report


def ensure_package(module_name, pip_name=None):
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            pip_name or module_name,
        ])
        return importlib.import_module(module_name)

