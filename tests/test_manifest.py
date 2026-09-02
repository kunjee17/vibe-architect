import pathlib
import tempfile
import unittest

from docsbase import frontmatter, manifest


def _g(paths=(), shapes=(), verify="source", status=None):
    return frontmatter.Governs(list(paths), list(shapes), verify, status)


class TestRoute(unittest.TestCase):
    def setUp(self):
        self.entries = [
            manifest.Entry("docs/architecture.md", _g(paths=["libs/domain/**"],
                                                      shapes=["actor"])),
            manifest.Entry("docs/design.md", _g(paths=["packages/ui/**"])),
            manifest.Entry("docs/product.md", _g(shapes=["scope"], verify="ask")),
        ]

    def test_glob_match_selects_doc(self):
        hits = manifest.route(self.entries, ["libs/domain/matters/src/lib.rs"], [])
        self.assertEqual([e.path for e in hits], ["docs/architecture.md"])

    def test_shape_match_selects_doc_with_no_paths(self):
        hits = manifest.route(self.entries, [], ["scope"])
        self.assertEqual([e.path for e in hits], ["docs/product.md"])

    def test_no_match_returns_empty(self):
        self.assertEqual(manifest.route(self.entries, ["README.md"], []), [])

    def test_multiple_hits_are_sorted_and_deduplicated(self):
        hits = manifest.route(
            self.entries,
            ["packages/ui/src/Button.tsx", "libs/domain/a/src/lib.rs"],
            ["actor"],
        )
        self.assertEqual(
            [e.path for e in hits], ["docs/architecture.md", "docs/design.md"]
        )

    def test_nested_glob_matches_at_any_depth(self):
        hits = manifest.route(self.entries, ["libs/domain/a/b/c/d.rs"], [])
        self.assertEqual([e.path for e in hits], ["docs/architecture.md"])


class TestCollectAndRender(unittest.TestCase):
    def test_collect_skips_non_authoritative_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = pathlib.Path(tmp)
            (docs / "architecture.md").write_text(
                "---\ngoverns:\n  paths: [src/**]\n---\n# A\n"
            )
            (docs / "vision.md").write_text("# Vision\n")
            entries = manifest.collect(docs)
            self.assertEqual([e.path for e in entries], ["architecture.md"])

    def test_render_is_stable_and_marks_the_generated_block(self):
        entries = [manifest.Entry("docs/product.md",
                                  _g(shapes=["scope"], verify="ask",
                                     status="stale - provisional"))]
        out = manifest.render(entries)
        self.assertIn(manifest.BEGIN, out)
        self.assertIn(manifest.END, out)
        self.assertIn("docs/product.md", out)
        self.assertIn("stale - provisional", out)
        self.assertIn("ask", out)
        self.assertEqual(out, manifest.render(entries))


if __name__ == "__main__":
    unittest.main()
