"""
Vercel serverless entrypoint for Mandate Radar FastAPI backend.
Vercel Python runtime natively handles ASGI applications when `app` is exposed.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
