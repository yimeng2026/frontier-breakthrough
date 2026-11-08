"""Cross-check the certified Hahn1 denominator with cvc5."""

import json
from pathlib import Path

from analyze_cvc5_crosscheck import run_cvc5, sha256

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation/cvc5-hahn1-denominator.json"
LOG = ROOT / "validation/cvc5-hahn1-denominator.log"


def main():
    output = run_cvc5("../../../../validation/cvc5-hahn1-denominator.smt2")
    result = output.strip().splitlines()[0].strip()
    if result != "unsat":
        raise ValueError(f"Expected unsat, got {result}: {output}")
    LOG.write_text(output, encoding="utf-8", newline="\n")
    z3 = json.loads((ROOT / "validation/z3-hahn1-denominator.json").read_text(encoding="utf-8"))
    if result != z3["result"]:
        raise ValueError("cvc5 and Z3 disagree")
    report = {
        "status": "verified",
        "result": result,
        "matches_z3": True,
        "denominator_positive_within_0_to_900": True,
        "domain": "0<=x<=900",
        "input_file": "validation/cvc5-hahn1-denominator.smt2",
        "log_file": "validation/cvc5-hahn1-denominator.log",
        "raw_output": output,
        "binary_sha256": sha256(ROOT / ".engines/cvc5-1.4.2/cvc5-Linux-x86_64-static/bin/cvc5"),
        "limitations": "The result applies only to the certified cubic denominator within 0<=x<=900; a positive root exists beyond the experimental range and no all-nonnegative-x claim is made",
    }
    if OUT.exists():
        previous = json.loads(OUT.read_text(encoding="utf-8"))
        if previous != report:
            raise ValueError("Refusing to overwrite a different cvc5 denominator result")
    else:
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
