# core/calendar.py

from datetime import datetime, date

import jdatetime
from django.utils import timezone


PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
ENGLISH_DIGITS = "0123456789"


def to_persian_digits(value):
    """
    تبدیل اعداد انگلیسی/عربی به اعداد فارسی
    """

    if value is None:
        return value

    value = str(value)

    translation_table = str.maketrans(
        ENGLISH_DIGITS + ARABIC_DIGITS,
        PERSIAN_DIGITS + PERSIAN_DIGITS,
    )

    return value.translate(
        translation_table
    )


def to_english_digits(value):
    """
    تبدیل اعداد فارسی/عربی به انگلیسی
    """

    if value is None:
        return value

    value = str(value)

    translation_table = str.maketrans(
        PERSIAN_DIGITS + ARABIC_DIGITS,
        ENGLISH_DIGITS + ENGLISH_DIGITS,
    )

    return value.translate(
        translation_table
    )


def gregorian_to_jalali(
    value,
    with_time=False,
    persian_digits=True,
):
    """
    تبدیل datetime/date میلادی به شمسی

    مثال:
    2026-08-18
    ->
    1405/05/27

    همراه ساعت:
    1405/05/27 09:30
    """

    if value is None:
        return None

    if isinstance(value, datetime):

        if timezone.is_aware(value):
            value = timezone.localtime(
                value
            )

        jalali = jdatetime.datetime.fromgregorian(
            datetime=value
        )

        if with_time:
            result = jalali.strftime(
                "%Y/%m/%d %H:%M"
            )
        else:
            result = jalali.strftime(
                "%Y/%m/%d"
            )

    elif isinstance(value, date):

        jalali = jdatetime.date.fromgregorian(
            date=value
        )

        result = jalali.strftime(
            "%Y/%m/%d"
        )

    else:
        return value

    if persian_digits:
        result = to_persian_digits(
            result
        )

    return result


def jalali_now(
    with_time=False,
    persian_digits=True,
):
    """
    تاریخ فعلی شمسی
    """

    return gregorian_to_jalali(
        timezone.localtime(),
        with_time=with_time,
        persian_digits=persian_digits,
    )


def jalali_to_gregorian(
    value,
):
    """
    تبدیل تاریخ شمسی به date میلادی

    ورودی قابل قبول:

    1405/05/27
    ۱۴۰۵/۰۵/۲۷
    1405-05-27
    """

    if not value:
        return None

    value = to_english_digits(
        value
    ).strip()

    value = value.replace(
        "-",
        "/"
    )

    parts = value.split("/")

    if len(parts) != 3:
        raise ValueError(
            "فرمت تاریخ شمسی باید YYYY/MM/DD باشد."
        )

    year = int(parts[0])
    month = int(parts[1])
    day = int(parts[2])

    jalali_date = jdatetime.date(
        year,
        month,
        day,
    )

    return jalali_date.togregorian()


def jalali_datetime_to_gregorian(
    value,
):
    """
    تبدیل تاریخ و ساعت شمسی به datetime میلادی

    مثال:

    1405/05/27 14:30
    """

    if not value:
        return None

    value = to_english_digits(
        value
    ).strip()

    value = value.replace(
        "-",
        "/"
    )

    date_part, *time_part = (
        value.split()
    )

    parts = date_part.split("/")

    if len(parts) != 3:
        raise ValueError(
            "فرمت تاریخ شمسی نامعتبر است."
        )

    year = int(parts[0])
    month = int(parts[1])
    day = int(parts[2])

    hour = 0
    minute = 0
    second = 0

    if time_part:

        time_values = time_part[0].split(
            ":"
        )

        if len(time_values) >= 1:
            hour = int(
                time_values[0]
            )

        if len(time_values) >= 2:
            minute = int(
                time_values[1]
            )

        if len(time_values) >= 3:
            second = int(
                time_values[2]
            )

    jalali_datetime = jdatetime.datetime(
        year,
        month,
        day,
        hour,
        minute,
        second,
    )

    gregorian_datetime = (
        jalali_datetime.togregorian()
    )

    return timezone.make_aware(
        gregorian_datetime
    )