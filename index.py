"""Vercel entrypoint: exposes the FastAPI app that lives in backend/app."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.main import app  # noqa: E402,F401
