from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

from icalendar import Calendar, Event
from lunar_python import Solar

from .config import (
    CALENDAR_DESCRIPTION,
    CALENDAR_NAME,
    PRODID,
    TIMEZONE,
)
from .holidays import (
    LUNAR_DAYS,
    LUNAR_HOLIDAYS,
    LUNAR_MONTHS,
    NEW_YEAR_EVE,
    QINGMING,
)


@lru_cache(maxsize=8192)
def _lunar_date(solar_date: date):
    return Solar.fromYmd(solar_date.year, solar_date.month, solar_date.day).getLunar()


def _build_event(solar_date: date, dtstamp: datetime) -> Event:
    lunar = _lunar_date(solar_date)
    lunar_month = abs(lunar.getMonth())
    lunar_day = lunar.getDay()
    holiday = LUNAR_HOLIDAYS.get((lunar_month, lunar_day))

    next_day = _lunar_date(solar_date + timedelta(days=1))
    if lunar_month == 12 and next_day.getDay() == 1 and next_day.getMonth() == 1:
        holiday = NEW_YEAR_EVE
    elif lunar.getJieQi() == "清明":
        holiday = QINGMING

    month_name = LUNAR_MONTHS[lunar_month]
    if lunar.getMonth() < 0:
        month_name = f"闰{month_name}"
    lunar_label = f"{month_name}{LUNAR_DAYS[lunar_day]}"
    summary = f"{lunar_label} · {holiday.name}" if holiday else lunar_label

    event = Event()
    event.add("uid", f"chinese-lunar-{solar_date:%Y%m%d}@cmduyeen")
    event.add("summary", summary)
    event.add("description", holiday.description if holiday else f"农历{lunar_label}")
    event.add("dtstart", solar_date)
    event.add("dtend", solar_date + timedelta(days=1))
    event.add("dtstamp", dtstamp)
    return event


class ChineseLunarCalendarGenerator:
    def generate_range(self, start_year: int, end_year: int) -> Calendar:
        if not 1 <= start_year <= end_year <= 9998:
            raise ValueError("年份范围必须满足 1 ≤ 开始年份 ≤ 结束年份 ≤ 9998。")

        calendar = Calendar()
        calendar.add("prodid", PRODID)
        calendar.add("version", "2.0")
        calendar.add("calscale", "GREGORIAN")
        calendar.add("method", "PUBLISH")
        calendar.add("x-wr-calname", f"{CALENDAR_NAME} {start_year}-{end_year}")
        calendar.add("x-wr-timezone", TIMEZONE)
        calendar.add("x-wr-caldesc", CALENDAR_DESCRIPTION)

        current = date(start_year, 1, 1)
        end = date(end_year, 12, 31)
        dtstamp = datetime.now(timezone.utc)
        while current <= end:
            calendar.add_component(_build_event(current, dtstamp))
            current += timedelta(days=1)
        return calendar

    @staticmethod
    def save(calendar: Calendar, filepath: str | Path) -> None:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(calendar.to_ical())
