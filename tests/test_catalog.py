import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
        cls.projects = cls.payload["projects"]

    def test_ids_are_unique_and_readable(self):
        ids = [p["id"] for p in self.projects]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(i == i.lower() and " " not in i for i in ids))

    def test_all_projects_have_upstream_and_contribution(self):
        for p in self.projects:
            self.assertTrue(p["source"].startswith("https://"), p["id"])
            self.assertGreater(len(p["collaboration"]), 12, p["id"])
            self.assertNotIn("已合作", p["collaboration"], p["id"])

    def test_strategic_projects_are_not_fake_local_installations(self):
        for p in self.projects:
            if p["adoption"] == "P3_external":
                self.assertIn(p["localStatus"], {"external", "deferred"})

    def test_catalog_is_not_described_as_exhaustive(self):
        text = (ROOT / "docs" / "GLOBAL_PROJECTS.md").read_text(encoding="utf-8")
        self.assertIn("不声称一次性穷尽全球", text)

    def test_required_research_domains_exist(self):
        domains = {p["domain"] for p in self.projects}
        self.assertTrue({"national", "math", "science", "biology", "physics", "infrastructure"} <= domains)


if __name__ == "__main__":
    unittest.main()
