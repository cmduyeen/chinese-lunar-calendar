import json
import re
import unittest
from datetime import date
from pathlib import Path

from src.engines import ENGINES
from src.ics import validate_bytes
from src.ics_generator import LunarCalendarGenerator
from src.localization import validate_translations
from src.profiles import PROFILES
from src.user_config import CalendarOptions

ROOT = Path(__file__).resolve().parents[1]
PROFILE = next(iter(PROFILES.values()))
ENGINE = ENGINES[PROFILE.engine]


class CountryTests(unittest.TestCase):
    def test_scope_and_translation_parity(self):
        self.assertEqual(list(PROFILES), ["CN"])
        validate_translations()
        expected = None
        for language in PROFILE.languages:
            options = CalendarOptions(language=language, content="festivals")
            calendar = LunarCalendarGenerator().generate_year(2026, options)
            parsed = validate_bytes(calendar.to_ical())
            actual = {
                (str(e["uid"]), e.decoded("dtstart"), str(e["x-lunar-event-id"]))
                for e in parsed.walk("VEVENT")
            }
            self.assertTrue(actual)
            if expected is None:
                expected = actual
            self.assertEqual(actual, expected)
            self.assertTrue(all(str(e["x-countries"]) == "CN" for e in parsed.walk("VEVENT")))
        with self.assertRaises(ValueError):
            CalendarOptions(country="KR")

    def test_independent_reference_dates(self):
        fixtures = json.loads(
            (ROOT / "tests/fixtures/reference_dates.json").read_text(encoding="utf-8")
        )
        for item in fixtures:
            if item["engine"] != PROFILE.engine:
                continue
            actual = ENGINE(date.fromisoformat(item["solar"]))
            self.assertEqual([actual.year, actual.month, actual.day, actual.leap], item["lunar"])

    def test_chinese_full_reference_tables(self):
        if PROFILE.engine != "chinese":
            return
        previous = None
        checked = 0
        for path in sorted((ROOT / "tests/fixtures").glob("hko-*.txt")):
            rows = []
            for line in path.read_text(encoding="utf-8-sig").splitlines():
                match = re.match(r"^(\d{4})/(\d{1,2})/(\d{1,2})\s+(.+?)\s{2,}", line)
                if match:
                    y, m, d, label = match.groups()
                    rows.append((date(int(y), int(m), int(d)), label.strip()))
            first_marker = next(
                int(re.match(r"(\d+)", label).group())
                for _, label in rows
                if "Lunar Month" in label
            )
            month = (first_marker - 2) % 12 + 1
            year = rows[0][0].year - 1
            leap = False
            if previous and previous[0].toordinal() + 1 == rows[0][0].toordinal():
                _, year, month, leap = previous
            for solar, label in rows:
                if "Lunar Month" in label:
                    following = int(re.match(r"(\d+)", label).group())
                    leap = following == month
                    month = following
                    day = 1
                    if month == 1 and not leap:
                        year = solar.year
                else:
                    day = int(label)
                actual = ENGINE(solar)
                self.assertEqual(
                    (actual.year, actual.month, actual.day, actual.leap), (year, month, day, leap)
                )
                checked += 1
                previous = (solar, year, month, leap)
        self.assertEqual(checked, 1825)

    def test_readme_urls_and_local_links(self):
        for page in ROOT.glob("README*.md"):
            text = page.read_text(encoding="utf-8")
            for link in re.findall(r"\]\(([^)]+)\)", text):
                if "://" in link or link.startswith("#"):
                    continue
                self.assertTrue((ROOT / link.split("#")[0]).exists(), link)
            urls = re.findall(r"```text\n(https://[^\n]+)\n```", text)
            if page.name == "README.zh-CN.md":
                continue
            self.assertTrue(urls)
            for url in urls:
                self.assertIn("/chinese-lunar-calendar/main/output/", url)
                self.assertTrue((ROOT / "output" / url.rsplit("/", 1)[1]).exists())

    def test_legacy_chinese_uid_and_leap_month_compatibility(self):
        if PROFILE.code != "CN":
            return
        from src.chinese_compat import _build_event
        from src.pipeline import INITIAL_REVISION

        event = _build_event(date(2028, 6, 27), INITIAL_REVISION)
        self.assertEqual(str(event["uid"]), "chinese-lunar-20280627@cmduyeen")
        self.assertNotIn("端午", str(event["summary"]))
