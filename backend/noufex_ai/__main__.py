"""Allow running: python -m noufex_ai"""
from __future__ import annotations

import sys


def main() -> None:
    import uvicorn
    from noufex_ai.settings import settings

    uvicorn.run(
        "noufex_ai.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
