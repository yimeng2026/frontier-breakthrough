"""Bound-safe text serialization for very large rational numbers."""

from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, localcontext

from exact_roots import as_fraction, fraction_text


def bounded_text(value):
    """Return exact fractions when practical, otherwise a bound-safe decimal.

    Large values are rounded away from zero, so a positive upper bound is never
    underestimated and a negative value never increases in magnitude.
    """
    value = as_fraction(value)
    if max(abs(value.numerator).bit_length(), value.denominator.bit_length()) <= 1024:
        return fraction_text(value)
    rounding = ROUND_CEILING if value >= 0 else ROUND_FLOOR
    with localcontext() as context:
        context.prec = 17
        context.rounding = rounding
        result = Decimal(value.numerator) / Decimal(value.denominator)
        return format(result, "e")
