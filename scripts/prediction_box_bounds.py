"""Exact pointwise prediction-shift bounds over certified denominator boxes."""

from exact_roots import as_fraction, evaluate


def pointwise_prediction_bound(numerator_coefficients, x, denominator_coefficients, standard_errors, radius, observed_y=None):
    """Bound |f_perturbed(x)-f_snapshot(x)| over the whole denominator box.

    The numerator is fixed. If R=radius*sum(sigma_j*|x|^j) and |D|-R>0,
    then |delta f| <= |N|*R/(|D|*(|D|-R)). With an observed y, the
    triangle inequality adds |y-f_snapshot| without assuming a distribution.
    """
    x = as_fraction(x)
    radius = as_fraction(radius)
    numerator_coefficients = [as_fraction(value) for value in numerator_coefficients]
    denominator_coefficients = [as_fraction(value) for value in denominator_coefficients]
    standard_errors = [as_fraction(value) for value in standard_errors]
    if len(standard_errors) != len(denominator_coefficients) - 1:
        raise ValueError("Scale count must match nonconstant denominator coefficients")
    if radius < 0:
        raise ValueError("Box radius must be nonnegative")
    numerator = evaluate(numerator_coefficients, x)
    denominator = evaluate(denominator_coefficients, x)
    if denominator == 0:
        raise ValueError("Snapshot denominator is zero at this point")
    perturbation = radius * sum(
        standard_errors[degree - 1] * abs(x) ** degree
        for degree in range(1, len(denominator_coefficients))
    )
    denominator_lower = abs(denominator) - perturbation
    if denominator_lower <= 0:
        raise ValueError("The denominator box is not certified away from zero at this point")
    shift = abs(numerator) * perturbation / (abs(denominator) * denominator_lower)
    snapshot_prediction = numerator / denominator
    residual_bound = None
    if observed_y is not None:
        residual_bound = abs(as_fraction(observed_y) - snapshot_prediction) + shift
    return {
        "snapshot_prediction": snapshot_prediction,
        "snapshot_denominator": denominator,
        "denominator_perturbation_bound": perturbation,
        "denominator_lower_bound": denominator_lower,
        "prediction_shift_upper_bound": shift,
        "absolute_residual_upper_bound": residual_bound,
    }
