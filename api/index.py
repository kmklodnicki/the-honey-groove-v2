"""Vercel Serverless Bridge — Root Directory = /
backend/ is a sibling of api/, so just add it to sys.path.
"""
import os
import sys

backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from server import app
