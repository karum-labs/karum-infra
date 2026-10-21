"""Print the Makefile's target list.

A target's description may span several ``## `` lines; they are merged into
one entry, so ``make help`` reads as a list of targets instead of a list of
fragments. Usage: python scripts/help.py <Makefile>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TARGET = re.compile(r"^##\s*([a-z][a-z0-9-]*):\s*(.*)$")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: help.py <Makefile>", file=sys.stderr)
        return 2
    entries: list[str] = []
    for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
        if not line.startswith("## "):
            continue
        match = TARGET.match(line)
        if match:
            entries.append(f"{match.group(1)}: {match.group(2)}".rstrip())
        elif entries:
            entries[-1] += " " + line[3:].strip()
    print(*entries, sep="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
