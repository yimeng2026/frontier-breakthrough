import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/external_coverage_scoped.py"
STALE = "The cubic/cubic candidate is only an approximation stress test and not the native Filip eleven-parameter model"


class ExternalCoverageScopedTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"Missing scoped external coverage adapter: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("external_coverage_scoped", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fake_summary(self):
        return {"analysis_scope": {}, "limitations": [STALE, "Keep this limitation"]}

    def test_mgh17_derives_native_scope_without_mutating_source_summary(self):
        module = self.load_module()
        original = self.fake_summary()
        received = copy.deepcopy(original)
        result = module.run_scoped_external_analysis(
            ROOT / "validation/mgh17-ellipsoid-coverage-protocol.json",
            runner_path=Path(__file__).resolve(),
            runner=lambda protocol_path, runner_path: received,
        )
        self.assertIn("MGH17", result["limitations"][0])
        self.assertIn("Five-parameter double-exponential class", result["limitations"][0])
        self.assertNotIn("Filip", result["limitations"][0])
        self.assertEqual(result["limitations"][1], "Keep this limitation")
        self.assertEqual(received, original)
        self.assertTrue(result["analysis_scope"]["dataset_specific_scope_text"])
        self.assertEqual(result["analysis_scope"]["scope_adapter_sha256"], hashlib.sha256(SCRIPT.read_bytes()).hexdigest())
        self.assertEqual(result["analysis_runner_sha256"], hashlib.sha256(Path(__file__).read_bytes()).hexdigest())

    def test_chwirut1_explicit_scope_and_related_dataset_boundary_win(self):
        module = self.load_module()
        protocol = json.loads((ROOT / "validation/chwirut1-ellipsoid-coverage-protocol.json").read_text(encoding="utf-8"))
        result = module.run_scoped_external_analysis(
            ROOT / "validation/chwirut1-ellipsoid-coverage-protocol.json",
            runner_path=Path(__file__).resolve(),
            runner=lambda protocol_path, runner_path: self.fake_summary(),
        )
        self.assertEqual(result["limitations"][0], protocol["candidate_rule"]["scope_limitation"])
        self.assertFalse(result["analysis_scope"]["independent_model_family_test"])
        self.assertEqual(result["analysis_scope"]["related_prior_dataset"], "Chwirut2")

    def test_driver_hash_mismatch_stops_before_runner(self):
        module = self.load_module()
        protocol = json.loads((ROOT / "validation/mgh17-ellipsoid-coverage-protocol.json").read_text(encoding="utf-8"))
        protocol.setdefault("implementation_rule", {})["driver_sha256"] = "0" * 64
        called = False
        def runner(protocol_path, runner_path):
            nonlocal called
            called = True
            return self.fake_summary()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "protocol.json"
            path.write_text(json.dumps(protocol), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "driver"):
                module.run_scoped_external_analysis(path, runner=runner)
        self.assertFalse(called)

    def test_adapter_hash_mismatch_stops_before_runner(self):
        module = self.load_module()
        protocol = json.loads((ROOT / "validation/mgh17-ellipsoid-coverage-protocol.json").read_text(encoding="utf-8"))
        protocol.setdefault("implementation_rule", {})["scope_adapter_sha256"] = "0" * 64
        called = False
        def runner(protocol_path, runner_path):
            nonlocal called
            called = True
            return self.fake_summary()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "protocol.json"
            path.write_text(json.dumps(protocol), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "adapter"):
                module.run_scoped_external_analysis(path, runner=runner)
        self.assertFalse(called)


if __name__ == "__main__":
    unittest.main()
