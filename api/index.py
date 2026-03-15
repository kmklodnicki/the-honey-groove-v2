"""Vercel Serverless Bridge
Adds /backend to sys.path so existing imports (from database import db, etc.)
resolve correctly whether running from Vercel (cwd=/) or Emergent (cwd=/backend).
"""
import os
import sys

# Ensure the backend package directory is on the Python path
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Export the FastAPI app directly (not the Socket.IO wrapper)
# Vercel serverless doesn't support WebSockets
from server import app
