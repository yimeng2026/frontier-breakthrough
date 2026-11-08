"""Exact Sturm root isolation with dual-solver checks for fifteen frozen folds."""

import hashlib
import importlib.metadata
import json
from pathlib import Path

from analyze_cvc5_crosscheck import run_cvc5
from exact_roots import as_fraction, exact_root_intervals, fraction_text, interval_record

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/rational-exact-interval-protocol.json"
OUT = ROOT / "validation/rational-exact-interval-roots.json"
SMT_DIR = ROOT / "validation/exact-interval-smt"
LOG_DIR = ROOT / "validation/exact-interval-logs"
FIGURE = ROOT / "papers/13_精确区间根证明/fig13_exact_interval_roots.png"
CVC5 = ROOT / ".engines/cvc5-1.4.2/cvc5-Linux-x86_64-static/bin/cvc5"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_inputs():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_exact_interval_root_analysis":
        raise ValueError("Exact interval protocol is not frozen")
    inputs = {}
    hashes = {}
    for key, info in protocol["inputs"].items():
        path = ROOT / info["file"]
        digest = sha256(path)
        if digest != info["sha256"]:
            raise ValueError(f"Input hash changed: {path}")
        inputs[key] = json.loads(path.read_text(encoding="utf-8"))
        hashes[key] = digest
    return protocol, inputs, hashes


def exact_case(dataset, fold, parameters, denominator_names, lower, upper, numerical_count):
    lower_value, upper_value = sorted([float(lower), float(upper)])
    coefficients = [1, *[parameters[name] for name in denominator_names]]
    intervals = exact_root_intervals(coefficients, lower_value, upper_value)
    exact_count = len(intervals)
    return {
        "dataset": dataset,
        "fold": fold,
        "model_parameters": parameters,
        "denominator_parameter_order": list(denominator_names),
        "closed_interval": [lower_value, upper_value],
        "closed_interval_rational": [fraction_text(lower_value), fraction_text(upper_value)],
        "numerical_root_count": numerical_count,
        "exact": {
            "method": "Exact rational Sturm sequence with squarefree gcd reduction, Cauchy bound and rational interval subdivision",
            "coefficient_snapshot_rational": [fraction_text(value) for value in coefficients],
            "root_count": exact_count,
            "isolating_intervals": [interval_record(interval) for interval in intervals],
            "matches_numerical_count": exact_count == numerical_count,
        },
    }


def analyze_exact():
    _, inputs, _ = load_inputs()
    cases = []
    hahn = inputs["hahn1_identifiability"]
    hahn_roots = inputs["hahn1_roots"]["folds"]
    for fold, roots in zip(hahn["folds"], hahn_roots):
        points = fold["held_out_points"]
        lower = min(point["x"] for point in points)
        upper = max(point["x"] for point in points)
        cases.append(exact_case(
            "hahn1", fold["fold"], fold["model_parameters"], ("b5", "b6", "b7"),
            lower, upper, roots["real_root_count_in_held_out_closed_interval"],
        ))
    for dataset in ["thurber", "kirby2"]:
        for fold in inputs[dataset]["folds"]:
            denominator_names = ("b5", "b6", "b7") if dataset == "thurber" else ("b4", "b5")
            domain = fold["domain_audit"]
            cases.append(exact_case(
                dataset, fold["fold"], fold["model_parameters"], denominator_names,
                *domain["closed_interval"], len(domain["real_roots_in_closed_interval"]),
            ))
    return cases


def rational_smt(value):
    value = as_fraction(value)
    numerator, denominator = value.numerator, value.denominator
    if numerator == 0:
        return "0"
    sign = "-" if numerator < 0 else ""
    numerator = abs(numerator)
    magnitude = str(numerator) if denominator == 1 else f"(/ {numerator} {denominator})"
    return f"({sign} {magnitude})" if sign else magnitude


def smt_term(coefficient, degree):
    coefficient = rational_smt(coefficient)
    if degree == 0:
        return coefficient
    return f"(* {coefficient} {' '.join(['x'] * degree)})"


def smt_document(case):
    coefficients = case["exact"]["coefficient_snapshot_rational"]
    expression = "(+ " + " ".join(smt_term(value, degree) for degree, value in enumerate(coefficients)) + ")"
    lines = [
        "(set-logic NRA)",
        "(declare-fun x () Real)",
        f"(assert (>= x {rational_smt(case['closed_interval_rational'][0])}))",
        f"(assert (<= x {rational_smt(case['closed_interval_rational'][1])}))",
        f"(assert (= {expression} 0))",
        "(check-sat)",
    ]
    if case["exact"]["root_count"] > 0:
        lines.append("(get-model)")
    return "\n".join(lines) + "\n"


def z3_check(case):
    from z3 import Real, RealVal, Solver

    x = Real("x")
    solver = Solver()
    solver.set(timeout=90000)
    solver.add(x >= RealVal(case["closed_interval_rational"][0]))
    solver.add(x <= RealVal(case["closed_interval_rational"][1]))
    denominator = RealVal("1")
    for degree, name in enumerate(case["denominator_parameter_order"], 1):
        denominator += RealVal(fraction_text(case["model_parameters"][name])) * x ** degree
    solver.add(denominator == 0)
    result = str(solver.check())
    model = str(solver.model()) if result == "sat" else ""
    log = f"result={result}\n" + (f"{model}\n" if model else "")
    return result, log


def validate_summary(summary):
    errors = []
    cases = summary.get("cases", [])
    if len(cases) != 15:
        errors.append("Expected fifteen exact interval cases")
    for case in cases:
        expected = "unsat" if case["exact"]["root_count"] == 0 else "sat"
        checks = case["solver_checks"]
        if checks["expected"] != expected or checks["z3"] != expected or checks["cvc5"] != expected:
            errors.append(f"Solver mismatch: {case['dataset']} fold {case['fold']}")
        if not case["exact"]["matches_numerical_count"]:
            errors.append(f"Exact/numerical count mismatch: {case['dataset']} fold {case['fold']}")
        for key in ["smt2", "z3_log", "cvc5_log"]:
            path = ROOT / checks[key]
            if not path.is_file() or sha256(path) != checks[f"{key}_sha256"]:
                errors.append(f"Missing or changed proof artifact: {path}")
    totals = summary.get("totals", {})
    for engine in ["z3", "cvc5"]:
        if totals.get(f"{engine}_unsat_count") != sum(case["solver_checks"][engine] == "unsat" for case in cases):
            errors.append(f"{engine} unsat total mismatch")
        if totals.get(f"{engine}_sat_count") != sum(case["solver_checks"][engine] == "sat" for case in cases):
            errors.append(f"{engine} sat total mismatch")
    if summary["decision"]["unresolved_or_disagreement_present"]:
        errors.append("Unresolved solver checks remain")
    if summary["decision"]["universal_denominator_safety_claimed"]:
        errors.append("Universal denominator safety claim detected")
    return errors


def main():
    if OUT.exists() or FIGURE.exists():
        raise FileExistsError("Refusing to overwrite existing exact interval proof outputs")
    protocol, _, input_hashes = load_inputs()
    if sha256(CVC5) != "6aecddf466552b83bb5883756c7955e0c9d5ddcc6d7f45b48c2f6e06a741b102":
        raise ValueError("cvc5 binary hash changed")
    SMT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    cases = analyze_exact()
    for case in cases:
        identifier = f"{case['dataset']}-fold-{case['fold']}"
        smt_path = SMT_DIR / f"{identifier}.smt2"
        smt_path.write_text(smt_document(case), encoding="utf-8", newline="\n")
        expected = "unsat" if case["exact"]["root_count"] == 0 else "sat"
        z3_result, z3_log = z3_check(case)
        z3_log_path = LOG_DIR / f"{identifier}-z3.log"
        z3_log_path.write_text(z3_log, encoding="utf-8", newline="\n")
        cvc5_output = run_cvc5(f"--tlimit 90000 --produce-models ../../../../validation/exact-interval-smt/{identifier}.smt2")
        cvc5_lines = [line.strip() for line in cvc5_output.splitlines() if line.strip()]
        cvc5_result = cvc5_lines[0] if cvc5_lines else "unknown"
        cvc5_log_path = LOG_DIR / f"{identifier}-cvc5.log"
        cvc5_log_path.write_text(cvc5_output, encoding="utf-8", newline="\n")
        case["solver_checks"] = {
            "expected": expected,
            "z3": z3_result,
            "cvc5": cvc5_result,
            "matches_exact_obligation": z3_result == expected and cvc5_result == expected,
            "smt2": smt_path.relative_to(ROOT).as_posix(),
            "smt2_sha256": sha256(smt_path),
            "z3_log": z3_log_path.relative_to(ROOT).as_posix(),
            "z3_log_sha256": sha256(z3_log_path),
            "cvc5_log": cvc5_log_path.relative_to(ROOT).as_posix(),
            "cvc5_log_sha256": sha256(cvc5_log_path),
        }
    unresolved = any(not case["solver_checks"]["matches_exact_obligation"] for case in cases)
    summary = {
        "status": "computed_exact_rational_sturm_and_dual_solver_checks",
        "protocol_sha256": sha256(PROTOCOL),
        "input_sha256": input_hashes,
        "coefficient_snapshot_scope": protocol["coefficient_snapshot_rule"],
        "z3_version": importlib.metadata.version("z3-solver"),
        "cvc5_version": run_cvc5("--version").splitlines()[0],
        "cvc5_binary_sha256": sha256(CVC5),
        "cases": cases,
        "totals": {
            "fold_count": len(cases),
            "exact_root_count_total": sum(case["exact"]["root_count"] for case in cases),
            "exact_no_root_fold_count": sum(case["exact"]["root_count"] == 0 for case in cases),
            "exact_rooted_fold_count": sum(case["exact"]["root_count"] > 0 for case in cases),
            "exact_numerical_count_match_count": sum(case["exact"]["matches_numerical_count"] for case in cases),
            "z3_unsat_count": sum(case["solver_checks"]["z3"] == "unsat" for case in cases),
            "z3_sat_count": sum(case["solver_checks"]["z3"] == "sat" for case in cases),
            "cvc5_unsat_count": sum(case["solver_checks"]["cvc5"] == "unsat" for case in cases),
            "cvc5_sat_count": sum(case["solver_checks"]["cvc5"] == "sat" for case in cases),
            "dual_solver_agreement_count": sum(case["solver_checks"]["matches_exact_obligation"] for case in cases),
        },
        "decision": {
            "unresolved_or_disagreement_present": unresolved,
            "all_exact_counts_match_numerical": all(case["exact"]["matches_numerical_count"] for case in cases),
            "approximate_sat_models_used_as_exact_proof": False,
            "universal_denominator_safety_claimed": False,
            "physical_parameter_exactness_claimed": False,
        },
        "limitations": [
            "Exact results concern the JSON decimal rational coefficient snapshots, not exact physical parameters or exact binary floating-point values",
            "Sturm isolation proves distinct real-root counts within each specified closed interval only",
            "Solver sat models are consistency witnesses, not exact algebraic root forms; Sturm intervals are the root-existence evidence",
            "No claim is made outside the specified intervals or for perturbed coefficients",
            "The two solver checks increase implementation confidence but do not replace the exact Sturm computation or independent review",
        ],
        "analysis_runner_sha256": sha256(Path(__file__).resolve()),
    }
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    errors = validate_summary(summary)
    if errors:
        raise ValueError(errors)

    print(json.dumps({
        "output": str(OUT),
        "totals": summary["totals"],
        "decision": summary["decision"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
