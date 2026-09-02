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

    def test_every_shipped_detector_names_a_known_extract_kind(self):
        known = {"glob-names", "json-keys", "line-prefix", "toml-list"}
        for row in detect.load_table():
            self.assertIn(row["extract"], known)

    def test_line_prefix_extracts_the_captured_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "Justfile").write_text("check:\n\techo hi\nbuild:\n\techo b\n")
            facts, _ = detect.derive(root)
            values = {f.value for f in facts if f.question == "gate-commands"}
            self.assertEqual(values, {"check", "build"})

    def test_a_bare_git_repo_does_not_answer_pre_commit_automation(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            facts, underived = detect.derive(root)
            hooks = [f for f in facts
                     if f.question == "pre-commit-automation"]
            self.assertEqual(hooks, [])
            self.assertIn("pre-commit-automation", underived)

    def test_toml_list_extracts_real_workspace_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "Cargo.toml").write_text(
                '[workspace]\nmembers = ["libs/a", "apps/b"]\n'
            )
            facts, underived = detect.derive(root)
            values = {f.value for f in facts if f.question == "units"}
            self.assertEqual(values, {"libs/a", "apps/b"})
            self.assertNotIn("units", underived)


if __name__ == "__main__":
    unittest.main()
