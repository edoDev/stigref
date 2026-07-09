import sys
from pathlib import Path

# Allow `pytest` from scripts/ without installing the package
SCRIPTS = Path(__file__).resolve().parent.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
