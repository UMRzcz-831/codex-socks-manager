from __future__ import annotations

import sys

from .paths import Paths
from .runtime import exec_real_codex


def main() -> None:
    exec_real_codex(Paths.discover(), sys.argv[1:])


if __name__ == "__main__":
    main()

