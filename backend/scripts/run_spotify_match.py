"""Standalone runner for Spotify batch matching — used by GitHub Actions cron."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.spotify_service import batch_match_releases


async def main():
    stop_event = asyncio.Event()
    result = await batch_match_releases(stop_event, run_limit=100, deadline_secs=800)
    print(
        f"processed={result['processed']} "
        f"matched={result['matched']} "
        f"unmatched={result['unmatched']} "
        f"rate_limited={result['rate_limited']}"
    )


asyncio.run(main())
