"""Cross-check the existing Z3 domain and identifiability obligations with cvc5."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / ".engines/cvc5-1.4.2/cvc5-Linux-x86_64-static/bin/cvc5"
ARCHIVE = ROOT / ".engines/cvc5-1.4.2.zip"
OUT = ROOT / "validation/cvc5-crosscheck.json"
WSL_BINARY = "/mnt/c/Users/一梦/Documents/kimi/workspace/frontier-breakthrough/.engines/cvc5-1.4.2/cvc5-Linux-x86_64-static/bin/cvc5"
CASES = [
    ("positive_denominator_by_contradiction", "validation/cvc5-positive-denominator.smt2", "unsat"),
    ("nonpositive_denominator_counterexample", "validation/cvc5-zero-denominator.smt2", "sat"),
    ("x_zero_parameter_nonidentifiability", "validation/cvc5-xzero-identifiability.smt2", "sat"),
]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_cvc5(arguments):
    command = f"cd {WSL_BINARY.rsplit('/', 1)[0]} && ./cvc5 {arguments}"
    completed = subprocess.run(
        ["wsl.exe", "--", "bash", "-lc", command],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", timeout=90, check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stdout)
    return completed.stdout


def main():
    if not BINARY.is_file():
        raise FileNotFoundError(BINARY)
    version = run_cvc5("--version").splitlines()[0]
    z3 = json.loads((ROOT / "validation/z3-identifiability.json").read_text(encoding="utf-8"))
    z3_by_id = {item["id"]: item["result"] for item in z3["checks"]}
    checks = []
    for identifier, relative, expected in CASES:
        output = run_cvc5(f"--produce-models ../../../../{relative}")
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        actual = lines[0] if lines else ""
        if actual != expected:
            raise ValueError(f"Unexpected cvc5 result for {identifier}: {actual!r}\n{output}")
        if actual != z3_by_id[identifier]:
            raise ValueError(f"Solver disagreement for {identifier}: cvc5={actual}, Z3={z3_by_id[identifier]}")
        log_path = ROOT / f"validation/cvc5-{identifier}.log"
        log_path.write_text(output, encoding="utf-8", newline="\n")
        checks.append({
            "id": identifier,
            "cvc5": actual,
            "z3": z3_by_id[identifier],
            "input_file": relative,
            "log_file": str(log_path.relative_to(ROOT)),
            "raw_output": output,
        })
    report = {
        "status": "verified",
        "solver_version": version,
        "official_release": "https://github.com/cvc5/cvc5/releases/tag/cvc5-1.4.2",
        "binary_sha256": sha256(BINARY),
        "official_archive_sha256": sha256(ARCHIVE),
        "binary_path": ".engines/cvc5-1.4.2/cvc5-Linux-x86_64-static/bin/cvc5",
        "execution": "WSL Ubuntu x86_64; official static cvc5 1.4.2 binary",
        "all_results_match_z3": all(item["cvc5"] == item["z3"] for item in checks),
        "checks": checks,
        "universal_identifiability_claimed": False,
        "limitations": [
            "Three finite SMT-LIB checks are cross-solver reproductions, not general nonlinear theorem proving",
            "The x=0 response is algebraically simplified before using either solver; no nonlinear exponential solver is claimed",
            "Agreement between two solvers increases implementation confidence only within the explicit formulas and domains",
        ],
    }
    if OUT.exists():
        previous = json.loads(OUT.read_text(encoding="utf-8"))
        if previous != report:
            raise ValueError("Refusing to overwrite a different cvc5 crosscheck")
    else:
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT), "version": version, "all_results_match_z3": report["all_results_match_z3"], "checks": [{key: item[key] for key in ["id", "cvc5", "z3"]} for item in checks]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
