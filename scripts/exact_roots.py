"""Exact real-root isolation for rational polynomials using Sturm sequences.

All arithmetic uses fractions.Fraction. Each returned open interval contains
exactly one distinct real root; exact roots at the requested closed-interval
endpoints are returned as singleton intervals. This is a root-location method,
not a floating-point approximation or an assertion about roots as closed forms.
"""

from fractions import Fraction


def as_fraction(value):
    return value if isinstance(value, Fraction) else Fraction(str(value))


def normalize(coefficients):
    values = [as_fraction(value) for value in coefficients]
    while len(values) > 1 and values[-1] == 0:
        values.pop()
    return values or [Fraction(0)]


def evaluate(coefficients, x):
    coefficients = normalize(coefficients)
    x = as_fraction(x)
    result = Fraction(0)
    for coefficient in reversed(coefficients):
        result = result * x + coefficient
    return result


def derivative(coefficients):
    coefficients = normalize(coefficients)
    return normalize([index * coefficient for index, coefficient in enumerate(coefficients)][1:] or [Fraction(0)])


def divide(coefficients, divisor):
    remainder = normalize(coefficients)
    divisor = normalize(divisor)
    if divisor == [0]:
        raise ZeroDivisionError("Polynomial division by zero")
    if len(remainder) < len(divisor):
        return [Fraction(0)], remainder
    quotient = [Fraction(0)] * (len(remainder) - len(divisor) + 1)
    while len(remainder) >= len(divisor) and remainder != [0]:
        shift = len(remainder) - len(divisor)
        factor = remainder[-1] / divisor[-1]
        quotient[shift] += factor
        for index, coefficient in enumerate(divisor):
            remainder[index + shift] -= factor * coefficient
        remainder = normalize(remainder)
    return normalize(quotient), remainder


def gcd(left, right):
    left, right = normalize(left), normalize(right)
    while right != [0]:
        _, remainder = divide(left, right)
        left, right = right, remainder
    if left == [0]:
        return left
    return normalize([coefficient / left[-1] for coefficient in left])


def squarefree(coefficients):
    coefficients = normalize(coefficients)
    if len(coefficients) <= 2:
        return coefficients
    common = gcd(coefficients, derivative(coefficients))
    quotient, remainder = divide(coefficients, common)
    if remainder != [0]:
        raise ArithmeticError("Exact squarefree division failed")
    return quotient


def sturm_sequence(coefficients):
    coefficients = squarefree(coefficients)
    if len(coefficients) <= 1:
        return [coefficients]
    sequence = [coefficients, derivative(coefficients)]
    while sequence[-1] != [0]:
        _, remainder = divide(sequence[-2], sequence[-1])
        if remainder == [0]:
            break
        sequence.append(normalize([-value for value in remainder]))
    return sequence


def variations(sequence, x):
    signs = []
    for polynomial in sequence:
        value = evaluate(polynomial, x)
        if value > 0:
            signs.append(1)
        elif value < 0:
            signs.append(-1)
    return sum(left != right for left, right in zip(signs, signs[1:]))


def nonzero_split(coefficients, lower, upper):
    midpoint = (lower + upper) / 2
    if evaluate(coefficients, midpoint) != 0:
        return midpoint
    for power in range(2, 80):
        delta = (upper - lower) / (2 ** power)
        for candidate in [midpoint - delta, midpoint + delta]:
            if lower < candidate < upper and evaluate(coefficients, candidate) != 0:
                return candidate
    raise ArithmeticError("Could not choose a non-root rational split")


def count_open(sequence, coefficients, lower, upper):
    if evaluate(coefficients, lower) == 0 or evaluate(coefficients, upper) == 0:
        raise ValueError("Sturm open-interval endpoints must not be roots")
    return variations(sequence, lower) - variations(sequence, upper)


def isolate_open(sequence, coefficients, lower, upper):
    count = count_open(sequence, coefficients, lower, upper)
    if count == 0:
        return []
    if count == 1:
        return [(lower, upper)]
    split = nonzero_split(coefficients, lower, upper)
    return isolate_open(sequence, coefficients, lower, split) + isolate_open(sequence, coefficients, split, upper)


def refine_to_closed(sequence, coefficients, lower, upper, target_lower, target_upper):
    if upper <= target_lower or lower >= target_upper:
        return []
    if lower >= target_lower and upper <= target_upper:
        return [(lower, upper)]
    if lower < target_lower < upper and evaluate(coefficients, target_lower) == 0:
        return [(target_lower, target_lower)]
    if lower < target_upper < upper and evaluate(coefficients, target_upper) == 0:
        return [(target_upper, target_upper)]
    split = nonzero_split(coefficients, lower, upper)
    refined = []
    if count_open(sequence, coefficients, lower, split) == 1:
        refined.extend(refine_to_closed(sequence, coefficients, lower, split, target_lower, target_upper))
    if count_open(sequence, coefficients, split, upper) == 1:
        refined.extend(refine_to_closed(sequence, coefficients, split, upper, target_lower, target_upper))
    return refined


def exact_root_intervals(coefficients, lower, upper):
    """Return isolating rational intervals for distinct roots in [lower, upper]."""
    coefficients = normalize(coefficients)
    lower, upper = as_fraction(lower), as_fraction(upper)
    if lower > upper:
        raise ValueError("Closed interval lower bound exceeds upper bound")
    if len(coefficients) <= 1:
        if coefficients == [0]:
            raise ValueError("The zero polynomial has infinitely many roots")
        return []
    if lower == upper:
        return [(lower, lower)] if evaluate(coefficients, lower) == 0 else []
    reduced = squarefree(coefficients)
    sequence = sturm_sequence(reduced)
    leading = reduced[-1]
    bound = 1 + max((abs(value / leading) for value in reduced[:-1]), default=Fraction(0))
    intervals = isolate_open(sequence, reduced, -bound, bound)
    refined = []
    for left, right in intervals:
        refined.extend(refine_to_closed(sequence, reduced, left, right, lower, upper))
    return sorted(set(refined))


def fraction_text(value):
    value = as_fraction(value)
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def interval_record(interval):
    lower, upper = interval
    return {
        "lower_rational": fraction_text(lower),
        "upper_rational": fraction_text(upper),
        "lower_float": float(lower),
        "upper_float": float(upper),
        "exact_singleton": lower == upper,
    }
