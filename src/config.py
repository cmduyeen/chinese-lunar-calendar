from datetime import datetime
from zoneinfo import ZoneInfo

DEFAULT_YEARS_AHEAD = 1
TIMEZONE = "Asia/Shanghai"
OUTPUT_DIR = "output"
CALENDAR_NAME = "中国"
CALENDAR_DESCRIPTION = "传统节日，不代表法定假日或调休安排。"
PRODID = "-//cmduyeen//Country Lunar Calendar//"
PUBLIC_FEED_BASE_URL = (
    "https://raw.githubusercontent.com/cmduyeen/chinese-lunar-calendar/main/output/"
)


def resolve_year_range(current_year, start_year=None, end_year=None, last_year=9998):
    """One default horizon for CLI, batch builds and custom configurations."""
    start = current_year if start_year is None else start_year
    end = min(start + DEFAULT_YEARS_AHEAD, last_year) if end_year is None else end_year
    if not 1 <= start <= end <= 9998:
        raise ValueError("years must satisfy 1 <= start <= end <= 9998")
    return start, end


START_YEAR = datetime.now(ZoneInfo(TIMEZONE)).year
END_YEAR = START_YEAR + 1

CALENDAR_NAME = "中国农历"
