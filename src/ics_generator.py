"""Country-scoped facade; no foreign profile or legacy engine is imported."""

import re

from icalendar import Calendar

from .ics import write_calendar
from .pipeline import generate
from .user_config import CalendarOptions


class LunarCalendarGenerator:
    def generate_range(self, start_year, end_year, options=None):
        return generate(start_year, end_year, options or CalendarOptions())

    def generate_year(self, year, options=None):
        return self.generate_range(year, year, options)

    @staticmethod
    def split_year(calendar, year):
        result = Calendar()
        for key, value in calendar.items():
            result[key] = value
        result["x-wr-calname"] = re.sub(
            r"\d{4}[â€“-]\d{4}$", str(year), str(calendar.get("x-wr-calname", "Calendar"))
        )
        for event in calendar.walk("VEVENT"):
            if event.decoded("dtstart").year == year:
                result.add_component(event)
        return result

    @staticmethod
    def save(calendar, filepath):
        return write_calendar(calendar, filepath)
