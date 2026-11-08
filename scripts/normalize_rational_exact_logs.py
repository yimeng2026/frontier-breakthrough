"""Normalize the initial unsat Z3 log serialization and refresh artifact hashes."""

import json

from prove_rational_interval_roots import OUT, sha256, validate_summary


def main():
    summary = json.loads(OUT.read_text(encoding="utf-8"))
    changed = []
    for case in summary["cases"]:
        checks = case["solver_checks"]
        if checks["z3"] != "unsat":
            continue
        path = OUT.parent / checks["z3_log"].removeprefix("validation/")
        canonical = "result=unsat\n"
        current = path.read_text(encoding="utf-8")
        if current != canonical:
            if current != canonical + "\n":
                raise ValueError(f"Unexpected Z3 log content: {path}")
            path.write_text(canonical, encoding="utf-8", newline="\n")
            changed.append(str(path))
        checks["z3_log_sha256"] = sha256(path)
    summary["analysis_runner_sha256"] = sha256(OUT.parent.parent / "scripts/prove_rational_interval_roots.py")
    errors = validate_summary(summary)
    if errors:
        raise ValueError(errors)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"normalized": changed, "count": len(changed)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
