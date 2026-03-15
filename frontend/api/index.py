"""Vercel Serverless Bridge for FastAPI
Root Directory = frontend/, so this file lives at frontend/api/index.py
"""
import os
import sys

# backend/ is sibling of frontend/ — go up two levels from this file
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from server import app
