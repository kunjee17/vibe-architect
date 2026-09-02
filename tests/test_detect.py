import pathlib
import tempfile
import unittest

from docsbase import detect


class TestDerive(unittest.TestCase):
    def test_zero_matches_still_works_and_reports_underived(self):
        with tempfile.TemporaryDirectory() as tmp:
            facts, underived = detect.derive(pathlib.Path(tmp))
            self.assertEqual(facts, [])
            self.assertEqual(set(underived), set(detect.QUESTIONS))

    def test_detects_a_glob_listing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / ".husky").mkdir()
            (root / ".husky" / "pre-commit").write_text("just check\n")
            facts, underived = detect.derive(root)
            hooks = [f for f in facts
                     if f.question == "pre-commit-automation"]
            self.assertEqual(len(hooks), 1)
            self.assertEqual(hooks[0].value, "pre-commit")
            self.assertEqual(hooks[0].source, ".husky/pre-commit")
            self.assertNotIn("pre-commit-automation", underived)

    def test_detects_json_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "package.json").write_text(
                '{"scripts": {"test": "vitest", "build": "tsc"}}'
            )
            facts, _ = detect.derive(root)
            values = {f.value for f in facts
                      if f.question == "gate-commands"}
            self.assertEqual(values, {"test", "build"})

    def test_a_detector_never_infers_from_an_unreadable_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "package.json").write_text("{ this is not json")
            facts, underived = detect.derive(root)
            self.assertEqual(
                [f for f in facts if f.question == "gate-commands"], []
            )
            self.assertIn("gate-commands", underived)

    def test_every_shipped_detector_names_a_known_question(self):
        for row in detect.load_table():
            self.assertIn(row["question"], detect.QUESTIONS)

    def test_every_fact_can_quote_its_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "Justfile").write_text("check:\n\techo hi\n")
            facts, _ = detect.derive(root)
            for f in facts:
                self.assertTrue(f.source)
                self.assertTrue((root / f.source.split(":")[0]).exists())


if __name__ == "__main__":
    unittest.main()
