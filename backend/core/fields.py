# core/fields.py

from rest_framework import serializers

from .calendar import (
    gregorian_to_jalali,
)


class JalaliDateTimeField(
    serializers.Field
):
    """
    نمایش DateTime به صورت شمسی
    """

    def __init__(
        self,
        *args,
        with_time=True,
        persian_digits=True,
        **kwargs,
    ):

        self.with_time = with_time

        self.persian_digits = (
            persian_digits
        )

        super().__init__(
            *args,
            read_only=True,
            **kwargs,
        )

    def to_representation(
        self,
        value,
    ):

        return gregorian_to_jalali(
            value,
            with_time=self.with_time,
            persian_digits=self.persian_digits,
        )