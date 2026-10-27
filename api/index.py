import sys
from pathlib import Path

# Add root folder to sys.path so app module is importable
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.main import app