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


class FieldMappingTests(unittest.TestCase):
    def test_exact_project_name_header_overrides_wrong_ai_alias_choice(self):
        class WrongAI:
            @staticmethod
            def field_mapping(headers, samples):
                return {
                    "name": {"column": 0, "confidence": 0.99, "reason": "误把工程名称当作项目名称"}
                }

        headers = ["工程名称", "项目编码", "项目名称", "项目特征描述", "计量单位", "工程量"]
        rows = [["桩基础工程(1)", "010302001001", "泥浆护壁成孔灌注桩", "桩径700mm", "m", 12595.5]]
        fields, mappings = ENGINE.infer_fields(headers, rows, WrongAI())

        self.assertEqual(fields["name"], 2)
        name_mapping = next(item for item in mappings if item["standardField"] == "name")
        self.assertEqual(name_mapping["sourceHeader"], "项目名称")
        self.assertEqual(name_mapping["confidence"], 100.0)
        self.assertEqual(name_mapping["method"], "标准表头精确匹配")


if __name__ == "__main__":
    unittest.main()
