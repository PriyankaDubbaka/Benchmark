"""Pre-commit guard: refuse to commit anything from the closed track.

Install once per clone with: git config core.hooksPath .githooks
"""
from __future__ import annotations

import subprocess
import sys

BLOCKED_PREFIX = "data/closed/"
ALLOWED = {"data/closed/README.md", "data/closed/.gitignore"}


def staged_files() -> list[str]:
    out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
                         capture_output=True, text=True, check=True).stdout
    return [l for l in out.splitlines() if l]


def blocked(paths: list[str]) -> list[str]:
    return [p for p in paths if p.startswith(BLOCKED_PREFIX) and p not in ALLOWED]


def main() -> int:
    bad = blocked(staged_files())
    if bad:
        print("Refusing to commit closed-track files (confidential reports must stay on BAM machines):")
        for p in bad:
            print("  " + p)
        print("Unstage them with: git restore --staged <file>")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
