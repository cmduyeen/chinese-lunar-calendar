"""Country calendar CLI; defaults to this repository's reviewed JSON profile."""

import sys
from pathlib import Path

from src.cli import main

if __name__ == "__main__":
    config = Path(__file__).resolve().with_name("calendar.config.json")
    raise SystemExit(main(["--config", str(config), *sys.argv[1:]]))
