"""Vercel Serverless Bridge
Sits inside frontend/api/ because Vercel Root Directory = frontend/
Adds the backend directory to sys.path so all existing imports resolve.
"""
import os
import sys

# backend/ is a sibling of frontend/ — go up one level from frontend/api/
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from server import app
