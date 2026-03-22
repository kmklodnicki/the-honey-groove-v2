"""Generates backend/release_info.json at Vercel build time.

Run as the first step of the buildCommand in vercel.json so the timestamp
captures the actual moment of deployment, not the first request.

Reads standard Vercel environment variables:
  VERCEL_GIT_COMMIT_SHA      — full commit hash
  VERCEL_GIT_COMMIT_MESSAGE  — commit message
  VERCEL_GIT_COMMIT_REF      — branch name
  VERCEL_ENV                 — production | preview | development
"""
import json
import os
import datetime
from pathlib import Path

info = {
    "deployed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "commit_sha": os.environ.get("VERCEL_GIT_COMMIT_SHA", "unknown"),
    "commit_message": os.environ.get("VERCEL_GIT_COMMIT_MESSAGE", ""),
    "branch": os.environ.get("VERCEL_GIT_COMMIT_REF", ""),
    "env": os.environ.get("VERCEL_ENV", "production"),
}

out = Path(__file__).parent.parent / "release_info.json"
out.write_text(json.dumps(info, indent=2))
print(f"release_info.json written: {info['deployed_at']} ({info['commit_sha'][:7]})")
