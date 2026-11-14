"""Only this country is enabled; no foreign profile is imported."""

import json
from dataclasses import dataclass
from pathlib import Path

FESTIVAL_SOURCES = json.loads(
    Path(__file__).with_name("festival_sources.json").read_text(encoding="utf-8")
)


@dataclass(frozen=True)
class Profile:
    code: str
    name: str
    timezone: str
    engine: str
    languages: tuple[str, ...]
    native: str
    tradition: str
    first_year: int
    last_year: int
    sources: tuple[str, ...]
    leap_festivals: bool = False


PROFILES = {
    "CN": Profile(
        code="CN",
        name="China",
        timezone="Asia/Shanghai",
        engine="chinese",
        languages=("zh-Hans", "en"),
        native="zh-Hans",
        tradition="chinese",
        first_year=1901,
        last_year=2099,
        sources=("https://www.hko.gov.hk/en/gts/time/conversion.htm",),
        leap_festivals=False,
    )
}
RULES = {
    "CN": (
        (1, 1, "lunar_new_year"),
        (1, 15, "lantern"),
        (5, 5, "dragon_boat"),
        (8, 15, "mid_autumn"),
        (1, 2, "cny_day_2"),
        (1, 3, "cny_day_3"),
        (2, 2, "dragon_heads"),
        (7, 7, "qixi"),
        (7, 15, "ghost"),
        (9, 9, "double_ninth"),
        (12, 8, "laba"),
        (12, 23, "xiaonian_north"),
        (12, 24, "xiaonian_south"),
    )
}
SOLAR_RULES = {"CN": ()}
SOLAR_TERMS = {"CN": {"清明": "qingming"}}
RESIDENCES = {}
ROADMAP = {}
GLOBAL_ROADMAP = {}


def get_profile(code):
    if not isinstance(code, str) or code.upper() not in PROFILES:
        raise ValueError(f"Unsupported lunar profile: {code}. Use --list-countries.")
    return PROFILES[code.upper()]


def resolve_language(profile, language, residence=None):
    language = ("en" if residence else profile.native) if language in (None, "native") else language
    supported = residence_languages(residence, profile) if residence else profile.languages
    if language not in supported:
        raise ValueError(
            f"{residence or profile.code} / {profile.tradition} supports languages: {', '.join(supported)}"
        )
    return language


def get_residence(code):
    if not isinstance(code, str) or code.upper() not in RESIDENCES:
        raise ValueError(f"Unsupported residence: {code}. Use --list-countries.")
    return RESIDENCES[code.upper()]


def residence_languages(residence, profile):
    host = get_residence(residence)
    if profile.code not in dict(host.traditions).values():
        raise ValueError(f"{host.code} does not support the {profile.code} profile")
    if profile.tradition == "chinese":
        return ("en", "zh-Hans", "zh-Hant")
    return ("en",) + tuple(lang for lang in profile.languages if lang != "en")
