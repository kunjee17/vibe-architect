import unittest

from docsbase import frontmatter


class TestParse(unittest.TestCase):
    def test_full_block(self):
        doc = (
            "---\n"
            "governs:\n"
            "  paths: [libs/domain/**, libs/actors/**]\n"
            "  shapes: [event-schema, actor]\n"
            "---\n\n# Architecture\n"
        )
        g = frontmatter.parse(doc)
        self.assertEqual(g.paths, ["libs/domain/**", "libs/actors/**"])
        self.assertEqual(g.shapes, ["event-schema", "actor"])
        self.assertEqual(g.verify, "source")
        self.assertIsNone(g.status)

    def test_no_frontmatter_is_not_authoritative(self):
        self.assertIsNone(frontmatter.parse("# Just a heading\n"))

    def test_frontmatter_without_governs_is_not_authoritative(self):
        self.assertIsNone(frontmatter.parse("---\ntitle: Vision\n---\n# Vision\n"))

    def test_verify_ask_and_status(self):
        doc = (
            "---\n"
            "governs:\n"
            "  shapes: [scope]\n"
            "  verify: ask\n"
            "status: stale - cost basis changed\n"
            "---\n# Product\n"
        )
        g = frontmatter.parse(doc)
        self.assertEqual(g.verify, "ask")
        self.assertEqual(g.paths, [])
        self.assertEqual(g.status, "stale - cost basis changed")

    def test_invalid_verify_raises(self):
        doc = "---\ngoverns:\n  verify: sometimes\n---\n"
        with self.assertRaises(frontmatter.ParseError):
            frontmatter.parse(doc)

    def test_unterminated_frontmatter_raises(self):
        with self.assertRaises(frontmatter.ParseError):
            frontmatter.parse("---\ngoverns:\n  paths: [a]\n")


if __name__ == "__main__":
    unittest.main()
