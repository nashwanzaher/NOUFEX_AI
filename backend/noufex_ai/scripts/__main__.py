"""Allow running: python -m noufex_ai.scripts seed"""
from __future__ import annotations

import sys


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] != "seed":
        print("Usage: python -m noufex_ai.scripts seed", file=sys.stderr)
        sys.exit(1)

    from noufex_ai.scripts.seed import seed

    import asyncio
    asyncio.run(seed())


if __name__ == "__main__":
    main()
