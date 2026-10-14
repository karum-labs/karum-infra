#!/usr/bin/env python3
"""Run `buf breaking` for the proto module against a base git commit.

The base commit is materialised with `git worktree` and passed to buf as a
plain directory. buf's `.git#branch=...` reference cannot be used here: git
references resolve against the repository root, while the buf module lives in
`proto/`, so buf would compare the wrong file tree.

Used by `make breaking` locally and by the Protos workflow in CI.

Usage:
    python scripts/breaking.py [--base <commit-or-ref>] [--buf <binary>]

Exits 0 when there are no breaking changes (or no base to compare against),
non-zero otherwise.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MODULE = REPO / "proto"
ZERO_SHA = "0" * 40


def run(cmd: list[str], cwd: Path = REPO, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, **kwargs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        default="origin/main",
        help="commit or ref to compare against (default: origin/main)",
    )
    parser.add_argument(
        "--buf",
        default="buf",
        help="buf binary to invoke (default: buf on PATH)",
    )
    args = parser.parse_args()

    base = args.base
    if not base or base == ZERO_SHA:
        print("breaking: no base commit to compare against; skipping.")
        return 0

    probe = run(
        ["git", "cat-file", "-e", f"{base}^{{commit}}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if probe.returncode != 0:
        # Shallow clones and force-pushes can leave the base unavailable.
        print(f"breaking: base {base!r} not available locally; skipping.")
        return 0

    # mkdtemp creates the parent; git worktree needs the child path to not
    # exist yet.
    scratch = Path(tempfile.mkdtemp(prefix="karum-breaking-"))
    worktree = scratch / "base"
    added = False
    try:
        add = run(
            ["git", "worktree", "add", "--detach", str(worktree), base]
        )
        if add.returncode != 0:
            print("breaking: could not materialise the base worktree.",
                  file=sys.stderr)
            return add.returncode
        added = True

        against = worktree / "proto"
        if not against.is_dir():
            print(f"breaking: proto/ does not exist in {base}.",
                  file=sys.stderr)
            return 1

        result = run(
            [args.buf, "breaking", f"--against={against.as_posix()}"],
            cwd=MODULE,
        )
        return result.returncode
    finally:
        if added:
            run(
                ["git", "worktree", "remove", "--force", str(worktree)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
