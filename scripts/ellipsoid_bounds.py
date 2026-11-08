"""Deterministic prediction bounds over covariance-defined denominator ellipsoids."""

from fractions import Fraction

from exact_roots import as_fraction, evaluate


def determinant(matrix):
    matrix = [[as_fraction(value) for value in row] for row in matrix]
    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise ValueError("Covariance matrix must be square")
    if size == 1:
        return matrix[0][0]
    if size == 2:
        return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    result = Fraction(0)
    for column, value in enumerate(matrix[0]):
        minor = [row[:column] + row[column + 1:] for row in matrix[1:]]
        result += (-1) ** column * value * determinant(minor)
    return result


def require_positive_definite(matrix):
    matrix = [[as_fraction(value) for value in row] for row in matrix]
    size = len(matrix)
    for row in range(size):
        for column in range(row + 1, size):
            if matrix[row][column] != matrix[column][row]:
                raise ValueError("Covariance matrix must be exactly symmetric")
    for order in range(1, size + 1):
        if determinant([row[:order] for row in matrix[:order]]) <= 0:
            raise ValueError("Covariance matrix is not positive definite")


def sqrt_upper(value):
    value = as_fraction(value)
    if value < 0:
        raise ValueError("Cannot take a real square root of a negative rational")
    if value == 0:
        return Fraction(0)
    numerator, denominator = value.numerator, value.denominator
    product = numerator * denominator
    from math import isqrt
    integer_root = isqrt(product)
    if integer_root * integer_root == product:
        return Fraction(integer_root, denominator)
    candidate = Fraction(integer_root + 1, denominator)
    for _ in range(6):
        candidate = (candidate + value / candidate) / 2
    if candidate * candidate < value:
        candidate += Fraction(1, denominator)
    return candidate


def covariance_support_upper_bound(covariance, powers):
    require_positive_definite(covariance)
    if len(powers) != len(covariance):
        raise ValueError("Power vector and covariance dimensions differ")
    powers = [as_fraction(value) for value in powers]
    variance = sum(
        powers[row] * powers[column] * as_fraction(covariance[row][column])
        for row in range(len(powers)) for column in range(len(powers))
    )
    if variance < 0:
        raise ValueError("Negative covariance support variance")
    return sqrt_upper(variance), variance


def pointwise_ellipsoid_bound(numerator_coefficients, x, denominator_coefficients, denominator_covariance, radius, observed_y=None):
    """Bound prediction shift for every denominator in a covariance ellipsoid."""
    x = as_fraction(x)
    radius = as_fraction(radius)
    numerator = evaluate(numerator_coefficients, x)
    denominator = evaluate(denominator_coefficients, x)
    if denominator == 0:
        raise ValueError("Snapshot denominator is zero")
    powers = [x ** degree for degree in range(1, len(denominator_coefficients))]
    support, variance = covariance_support_upper_bound(denominator_covariance, powers)
    perturbation = radius * support
    denominator_lower = abs(denominator) - perturbation
    if denominator_lower <= 0:
        raise ValueError("The covariance ellipsoid is not certified away from zero at this point")
    shift = abs(numerator) * perturbation / (abs(denominator) * denominator_lower)
    snapshot_prediction = numerator / denominator
    residual_bound = None
    if observed_y is not None:
        residual_bound = abs(as_fraction(observed_y) - snapshot_prediction) + shift
    return {
        "snapshot_prediction": snapshot_prediction,
        "snapshot_denominator": denominator,
        "covariance_support_variance": variance,
        "covariance_support_upper_bound": support,
        "denominator_perturbation_bound": perturbation,
        "denominator_lower_bound": denominator_lower,
        "prediction_shift_upper_bound": shift,
        "absolute_residual_upper_bound": residual_bound,
    }
