from __future__ import annotations

import argparse
import shutil
import sys
from datetime import date
from pathlib import Path

from src.calendar_generator import ChineseLunarCalendarGenerator
from src.config import DEFAULT_YEARS_AHEAD, OUTPUT_DIR


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Generate a Chinese lunar calendar in iCalendar format."
    )
    parser.add_argument("--start", type=int, help="First Gregorian year.")
    parser.add_argument("--end", type=int, help="Last Gregorian year.")
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent / OUTPUT_DIR),
        help="Output directory.",
    )
    args = parser.parse_args()

    start_year = args.start if args.start is not None else date.today().year
    end_year = (
        args.end
        if args.end is not None
        else start_year + DEFAULT_YEARS_AHEAD
    )
    if not 1 <= start_year <= end_year <= 9998:
        parser.error("years must satisfy 1 <= start <= end <= 9998")

    output_dir = Path(args.output_dir)
    suffix = f"{start_year}_{end_year}"
    range_file = output_dir / f"chinese_lunar_{suffix}.ics"
    latest_file = output_dir / "chinese_lunar_latest.ics"

    calendar = ChineseLunarCalendarGenerator().generate_range(start_year, end_year)
    ChineseLunarCalendarGenerator.save(calendar, range_file)
    shutil.copyfile(range_file, latest_file)
    print(f"Generated {range_file} and {latest_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
