"""Exact continuous-interval certificates for covariance-ellipsoid denominators."""

from exact_roots import as_fraction, evaluate, exact_root_intervals, fraction_text, interval_record
from ellipsoid_bounds import require_positive_definite


def polynomial_multiply(left, right):
    left = [as_fraction(value) for value in left]
    right = [as_fraction(value) for value in right]
    result = [as_fraction(0) for _ in range(len(left) + len(right) - 1)]
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            result[i + j] += a * b
    return result


def support_variance_coefficients(covariance, degree):
    require_positive_definite(covariance)
    result = [as_fraction(0) for _ in range(2 * degree + 1)]
    for row in range(degree):
        for column in range(degree):
            result[row + column + 2] += as_fraction(covariance[row][column])
    return result


def certify_ellipsoid_interval(coefficients, covariance, radius, lower, upper):
    coefficients = [as_fraction(value) for value in coefficients]
    lower, upper, radius = as_fraction(lower), as_fraction(upper), as_fraction(radius)
    if lower > upper or radius < 0:
        raise ValueError("Invalid interval or ellipsoid radius")
    snapshot_value = evaluate(coefficients, lower)
    if snapshot_value == 0:
        return {
            "snapshot_safe": False,
            "continuous_ellipsoid_safe": False,
            "reason": "Snapshot denominator is zero at the lower endpoint",
        }
    sign = 1 if snapshot_value > 0 else -1
    snapshot_roots = exact_root_intervals(coefficients, lower, upper)
    snapshot_safe = not snapshot_roots and sign * snapshot_value > 0
    positive_denominator = [sign * value for value in coefficients]
    squared_denominator = polynomial_multiply(positive_denominator, positive_denominator)
    variance = support_variance_coefficients(covariance, len(coefficients) - 1)
    support_polynomial = [
        squared_denominator[index] - radius ** 2 * variance[index]
        for index in range(len(squared_denominator))
    ]
    support_roots = exact_root_intervals(support_polynomial, lower, upper)
    support_safe = not support_roots and evaluate(support_polynomial, lower) > 0
    return {
        "snapshot_safe": snapshot_safe,
        "continuous_ellipsoid_safe": bool(snapshot_safe and support_safe),
        "snapshot_root_count": len(snapshot_roots),
        "support_polynomial_root_count": len(support_roots),
        "support_polynomial_coefficients_rational": [fraction_text(value) for value in support_polynomial],
        "support_polynomial_roots": [interval_record(interval) for interval in support_roots],
        "support_variance_coefficients_rational": [fraction_text(value) for value in variance],
        "reason": "Exact squared-support certificate: D^2-rho^2*z^T*Sigma*z>0 and sign-consistent D on the closed interval; non-certification is not called unsafe",
    }


def certify_positive_polynomial(coefficients, lower, upper):
    intervals = exact_root_intervals(coefficients, lower, upper)
    return not intervals and evaluate(coefficients, lower) > 0
