import importlib.util
import unittest
from pathlib import Path


ENGINE_PATH = Path(__file__).resolve().parents[4] / "platform" / "scripts" / "cost-engine.py"
SPEC = importlib.util.spec_from_file_location("cost_engine", ENGINE_PATH)
ENGINE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENGINE)


class MatchingRetrievalTests(unittest.TestCase):
    def setUp(self):
        self.catalog = [
            {"code": f"C{index:03d}", "name": f"普通候选项目{index}", "unit": "m3"}
            for index in range(40)
        ]
        self.correct = {"code": "RIGHT", "name": "现浇混凝土独立基础", "unit": "m3"}
        self.catalog.append(self.correct)

    def test_ai_query_expansion_can_recover_item_outside_initial_candidates(self):
        initial = ENGINE.top_matches("完全无关描述", "m3", self.catalog, 5)
        self.assertNotIn("RIGHT", {item["code"] for _, item in initial})

        expanded = ENGINE.expanded_matches(
            ["完全无关描述", "现浇混凝土独立基础"], "m3", self.catalog, initial, [], 30
        )
        self.assertIn("RIGHT", {item["code"] for _, item in expanded})

    def test_valid_ai_code_is_injected_from_complete_catalog(self):
        initial = ENGINE.top_matches("完全无关描述", "m3", self.catalog, 5)
        expanded = ENGINE.expanded_matches(
            ["完全无关描述"], "m3", self.catalog, initial, ["RIGHT"], 30
        )
        score, item = next(entry for entry in expanded if entry[1]["code"] == "RIGHT")
        self.assertEqual(item, self.correct)
        self.assertEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
