# server/app.py — OpenEnv server entry point
# Required by openenv validate. Re-exports the FastAPI app from main.py.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from main import app

__all__ = ["app"]
