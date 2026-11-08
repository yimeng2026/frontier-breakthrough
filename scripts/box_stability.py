"""Exact sufficient no-root proofs for boxes of rational denominator coefficients."""

from fractions import Fraction

from exact_roots import as_fraction, evaluate, exact_root_intervals, fraction_text


def certified_box_safe(coefficients, standard_errors, lower, upper, radius):
    """Return True only when every coefficient in the scaled box is root-free.

    The box is |delta c_j| <= radius * standard_errors[j]. The proof uses
    sign(D(x))*D_perturbed(x) >= sign(D(x))*D(x)-radius*sum(se_j*|x|^j).
    Positivity of the right-hand side on the whole closed interval is sufficient.
    """
    coefficients = [as_fraction(value) for value in coefficients]
    standard_errors = [as_fraction(value) for value in standard_errors]
    lower, upper, radius = as_fraction(lower), as_fraction(upper), as_fraction(radius)
    if len(standard_errors) != len(coefficients) - 1:
        raise ValueError("One standard-error scale is required per nonconstant coefficient")
    if any(value < 0 for value in standard_errors) or radius < 0 or lower > upper:
        raise ValueError("Invalid box radius, scale or interval")
    if lower < 0 < upper:
        return certified_box_safe(coefficients, standard_errors, lower, 0, radius) and certified_box_safe(coefficients, standard_errors, 0, upper, radius)
    snapshot = evaluate(coefficients, lower)
    if snapshot == 0:
        return False
    sign = 1 if snapshot > 0 else -1
    positive_x = lower >= 0
    perturbed = []
    for degree, coefficient in enumerate(coefficients):
        if degree == 0:
            perturbed.append(sign * coefficient)
            continue
        absolute_weight = Fraction(1) if positive_x else Fraction((-1) ** degree)
        perturbed.append(sign * coefficient - radius * standard_errors[degree - 1] * absolute_weight)
    if not exact_root_intervals(perturbed, lower, upper):
        return evaluate(perturbed, lower) > 0
    return False


def certify_parameter_box_radius(coefficients, standard_errors, lower, upper, cap=4, iterations=24):
    """Conservatively bracket the largest sufficient box radius, in scale units."""
    cap = as_fraction(cap)
    if not certified_box_safe(coefficients, standard_errors, lower, upper, 0):
        return {
            "snapshot_safe": False,
            "certified_region_safe": False,
            "certified_radius_lower_bound": Fraction(0),
            "certified_radius_lower_bound_float": 0.0,
            "uncertified_radius_upper_bound": None,
            "uncertified_radius_upper_bound_float": None,
            "cap_hit": False,
            "reason": "The unperturbed snapshot already has a root or changes sign in the closed interval",
        }
    if certified_box_safe(coefficients, standard_errors, lower, upper, cap):
        return {
            "snapshot_safe": True,
            "certified_region_safe": True,
            "certified_radius_lower_bound": cap,
            "certified_radius_lower_bound_rational": fraction_text(cap),
            "certified_radius_lower_bound_float": float(cap),
            "uncertified_radius_upper_bound": None,
            "uncertified_radius_upper_bound_float": None,
            "cap_hit": True,
            "reason": "The entire capped box is certified; the radius may be larger but was not tested beyond the cap",
        }
    lower_bound, upper_bound = Fraction(0), cap
    for _ in range(iterations):
        midpoint = (lower_bound + upper_bound) / 2
        if certified_box_safe(coefficients, standard_errors, lower, upper, midpoint):
            lower_bound = midpoint
        else:
            upper_bound = midpoint
    return {
        "snapshot_safe": True,
        "certified_region_safe": lower_bound > 0,
        "certified_radius_lower_bound": lower_bound,
        "certified_radius_lower_bound_rational": fraction_text(lower_bound),
        "certified_radius_lower_bound_float": float(lower_bound),
        "uncertified_radius_upper_bound": upper_bound,
        "uncertified_radius_upper_bound_rational": fraction_text(upper_bound),
        "uncertified_radius_upper_bound_float": float(upper_bound),
        "cap_hit": False,
        "reason": "Lower bound is certified for the whole box; upper bound is not certified and is not asserted unsafe",
    }
