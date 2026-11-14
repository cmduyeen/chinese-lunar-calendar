from functools import lru_cache

from lunar_python import Solar

from .models import LunarDay


@lru_cache(maxsize=16384)
def chinese(day):
    lunar = Solar.fromYmd(day.year, day.month, day.day).getLunar()
    return LunarDay(
        day,
        lunar.getYear(),
        abs(lunar.getMonth()),
        lunar.getDay(),
        lunar.getMonth() < 0,
        lunar.getJieQi(),
    )


ENGINES = {"chinese": chinese}
