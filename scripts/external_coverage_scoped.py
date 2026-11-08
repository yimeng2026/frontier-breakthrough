"""Scope-aware adapter for the frozen external coverage driver.

The original driver and its frozen outputs are not modified. New protocols can
use this adapter to enforce implementation hashes and dataset-specific scope.
"""

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = Path(__file__).resolve()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def scope_limitation(protocol):
    explicit = protocol.get("candidate_rule", {}).get("scope_limitation")
    if explicit:
        return explicit
    scope = protocol["dataset_scope"]
    label = scope["name"].split()[-1]
    native_description = scope["native_model"].split(";", 1)[0].split(":", 1)[0].strip()
    return f"The cubic/cubic candidate is only an approximation stress test and not the native {label} model: {native_description}"


def apply_scope_limitations(summary, protocol, runner_path=None):
    scoped = copy.deepcopy(summary)
    scoped["limitations"][0] = scope_limitation(protocol)
    scoped["analysis_scope"]["dataset_specific_scope_text"] = True
    scoped["analysis_scope"]["scope_adapter"] = "scripts/external_coverage_scoped.py"
    scoped["analysis_scope"]["scope_adapter_sha256"] = sha256(ADAPTER_PATH)
    related = protocol["dataset_scope"].get("related_prior_dataset")
    if related:
        scoped["analysis_scope"]["independent_model_family_test"] = False
        scoped["analysis_scope"]["related_prior_dataset"] = related["name"]
    if "analysis_runner_sha256" not in scoped and runner_path is not None:
        scoped["analysis_runner_sha256"] = sha256(runner_path)
    return scoped


def run_scoped_external_analysis(protocol_path, runner_path=None, runner=None):
    protocol_path = Path(protocol_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    implementation = protocol.get("implementation_rule", {})
    if "driver_sha256" in implementation:
        driver_path = ROOT / implementation.get("driver", "scripts/external_coverage.py")
        if sha256(driver_path) != implementation["driver_sha256"]:
            raise ValueError(f"External coverage driver hash changed: {driver_path}")
    if "scope_adapter_sha256" in implementation and sha256(ADAPTER_PATH) != implementation["scope_adapter_sha256"]:
        raise ValueError("External scope adapter hash changed")
    if runner is None:
        from external_coverage import run_external_analysis as runner
    runner_path = ADAPTER_PATH if runner_path is None else Path(runner_path)
    summary = runner(protocol_path, runner_path)
    return apply_scope_limitations(summary, protocol, runner_path)
