import contextlib
import importlib.util
import io
import os
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "build_manifest", ROOT / "bin" / "build-manifest.py"
)
build_manifest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_manifest)


class TestCli(unittest.TestCase):
    def _repo(self, tmp):
        root = pathlib.Path(tmp)
        (root / "docs").mkdir()
        (root / "docs" / "architecture.md").write_text(
            "---\ngoverns:\n  paths: [src/**]\n---\n# A\n"
        )
        return root

    def test_build_writes_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            build_manifest.write(root)
            text = (root / "docs" / "MANIFEST.md").read_text()
            self.assertIn("architecture.md", text)

    def test_check_passes_when_current(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            build_manifest.write(root)
            self.assertTrue(build_manifest.check(root))

    def test_check_fails_when_a_doc_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            build_manifest.write(root)
            (root / "docs" / "design.md").write_text(
                "---\ngoverns:\n  paths: [ui/**]\n---\n# D\n"
            )
            self.assertFalse(build_manifest.check(root))

    def test_check_fails_when_manifest_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            self.assertFalse(build_manifest.check(root))

    def test_malformed_frontmatter_reports_one_line_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "bad.md").write_text(
                "---\ngoverns:\n  verify: sometimes\n---\n"
            )
            cwd = pathlib.Path.cwd()
            os.chdir(root)
            try:
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    code = build_manifest.main([])
            finally:
                os.chdir(cwd)
            self.assertEqual(code, 1)
            self.assertIn("error:", err.getvalue())
            self.assertNotIn("Traceback", err.getvalue())


if __name__ == "__main__":
    unittest.main()
