#!/usr/bin/env python3
"""Create directories, the way `mkdir -p` does, on every platform.

Usage:
    python scripts/mkdir_p.py <dir> [<dir> ...]

The Makefile calls this instead of `python -c "import pathlib; ..."`: make's
Windows shell (cmd.exe) mangles a quoted `-c` string after a leading `.venv`
segment, and `mkdir -p` does not exist on cmd.exe.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: mkdir_p.py <dir> [<dir> ...]", file=sys.stderr)
        return 2
    for item in argv:
        Path(item).mkdir(parents=True, exist_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
