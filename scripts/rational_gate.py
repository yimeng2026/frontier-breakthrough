"""Shared numerical diagnostics for rational models with a unit denominator constant.

The caller supplies the original model callable, so fitting arithmetic and frozen
model definitions remain under the dataset-specific modules' control.
"""

import numpy as np

from analyze_chwirut_holdout import error_metrics


def rational_denominator(x, parameters, denominator_parameters):
    x = np.asarray(x, dtype=float)
    denominator = np.ones_like(x)
    for degree, name in enumerate(denominator_parameters, 1):
        denominator = denominator + parameters[name] * x ** degree
    return denominator


def rational_jacobian(x, parameters, numerator_parameters, denominator_parameters, model):
    x = np.asarray(x, dtype=float)
    names = tuple(numerator_parameters) + tuple(denominator_parameters)
    prediction = model(x, *[parameters[name] for name in names])
    denominator = rational_denominator(x, parameters, denominator_parameters)
    jacobian = np.empty((x.size, len(names)), dtype=float)
    for column, degree in enumerate(range(len(numerator_parameters))):
        jacobian[:, column] = x ** degree / denominator
    offset = len(numerator_parameters)
    for column, degree in enumerate(range(1, len(denominator_parameters) + 1), offset):
        jacobian[:, column] = -prediction * x ** degree / denominator
    return jacobian


def rational_root_records(parameters, numerator_parameters, denominator_parameters):
    numerator_coefficients = [parameters[name] for name in numerator_parameters]
    denominator_coefficients = [parameters[name] for name in denominator_parameters]
    roots = np.roots([*reversed(denominator_coefficients), 1.0])
    records = []
    for root in sorted(roots, key=lambda item: (float(item.real), float(item.imag))):
        is_real = bool(abs(root.imag) < 1.0e-8)
        record = {"root_real": float(root.real), "root_imag": float(root.imag), "is_real": is_real}
        if is_real:
            x = float(root.real)
            numerator = sum(value * x ** degree for degree, value in enumerate(numerator_coefficients))
            denominator = 1.0 + sum(value * x ** degree for degree, value in enumerate(denominator_coefficients, 1))
            derivative = sum(degree * value * x ** (degree - 1) for degree, value in enumerate(denominator_coefficients, 1))
            record.update({
                "root_x": x,
                "absolute_denominator_residual": float(abs(denominator)),
                "numerator_at_root": float(numerator),
                "denominator_derivative_at_root": float(derivative),
                "numerical_simple_pole_evidence": bool(numerator != 0 and derivative != 0),
                "interpretation": "Nonzero numerator and first derivative at a numerical real root support a simple-pole diagnosis, not an exact algebraic proof",
            })
        records.append(record)
    return records


def assess_prediction_domain(parameters, test_x, model, numerator_parameters, denominator_parameters):
    test_x = np.asarray(test_x, dtype=float)
    lower, upper = float(np.min(test_x)), float(np.max(test_x))
    names = tuple(numerator_parameters) + tuple(denominator_parameters)
    roots = rational_root_records(parameters, numerator_parameters, denominator_parameters)
    inside = [root for root in roots if root["is_real"] and lower <= root["root_x"] <= upper]
    grid = np.linspace(lower, upper, 1001)
    grid_denominator = rational_denominator(grid, parameters, denominator_parameters)
    test_denominator = rational_denominator(test_x, parameters, denominator_parameters)
    prediction = model(test_x, *[parameters[name] for name in names])
    sign_changes = np.signbit(grid_denominator[:-1]) != np.signbit(grid_denominator[1:])
    finite = bool(np.isfinite(prediction).all() and np.isfinite(test_denominator).all() and np.isfinite(grid_denominator).all())
    nonzero = bool(np.all(test_denominator != 0) and np.all(grid_denominator != 0))
    return {
        "closed_interval": [lower, upper],
        "grid_point_count": int(grid.size),
        "real_roots_in_closed_interval": [root["root_x"] for root in inside],
        "real_root_records_in_closed_interval": inside,
        "grid_denominator_sign_change_count": int(np.sum(sign_changes)),
        "grid_min_absolute_denominator": float(np.min(np.abs(grid_denominator))),
        "test_min_absolute_denominator": float(np.min(np.abs(test_denominator))),
        "all_predictions_and_denominators_finite": finite,
        "all_denominators_nonzero": nonzero,
        "domain_admissible": bool(finite and nonzero and not inside and not np.any(sign_changes)),
        "interpretation": "Numerical admissibility on this closed held-out interval, not an exact algebraic proof outside it",
    }


def local_identifiability(x, y, parameters, model, numerator_parameters, denominator_parameters):
    names = tuple(numerator_parameters) + tuple(denominator_parameters)
    prediction = model(x, *[parameters[name] for name in names])
    residual = y - prediction
    jacobian = rational_jacobian(x, parameters, numerator_parameters, denominator_parameters, model)
    norms = np.linalg.norm(jacobian, axis=0)
    if np.any(norms <= 0) or not np.isfinite(jacobian).all():
        raise ValueError("Invalid training Jacobian")
    scaled = jacobian / norms
    singular_values = np.linalg.svd(scaled, compute_uv=False)
    tolerance = max(jacobian.shape) * np.finfo(float).eps * singular_values[0]
    rank = int(np.sum(singular_values > tolerance))
    unit_covariance = np.linalg.pinv(scaled.T @ scaled, rcond=1.0e-12, hermitian=True)
    sigma2 = float(residual @ residual) / (len(x) - len(names))
    covariance = sigma2 * unit_covariance / np.outer(norms, norms)
    standard_errors = np.sqrt(np.maximum(np.diag(covariance), 0.0))
    correlation = np.clip(covariance / np.outer(standard_errors, standard_errors), -1.0, 1.0)
    return {
        "numerical_rank": rank,
        "numerical_rank_tolerance": float(tolerance),
        "scaled_singular_values": singular_values.tolist(),
        "scaled_condition_number": float(singular_values[0] / singular_values[-1]),
        "local_standard_errors": dict(zip(names, map(float, standard_errors))),
        "max_absolute_off_diagonal_parameter_correlation": float(np.max(np.abs(correlation - np.eye(len(names))))),
        "minimal_numerical_identifiability": bool(rank == len(names) and np.isfinite(standard_errors).all() and np.all(standard_errors > 0)),
        "training_metrics": error_metrics(y, prediction),
        "interpretation": "Minimal local numerical check; full rank does not establish global identifiability or physical endogeneity",
    }
