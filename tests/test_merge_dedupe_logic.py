import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import merge_zotero_duplicates as merge  # noqa: E402


FIXTURE_PATH = ROOT / "tests" / "fixtures" / "merge_dedupe_fixture.json"


class MergeDedupeLogicTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fx = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_canonical_group_key_priority(self) -> None:
        doi_key = merge.canonical_group_key(self.fx["doi_case"], "auto")
        url_key = merge.canonical_group_key(self.fx["url_case"], "auto")
        title_key = merge.canonical_group_key(self.fx["title_case"], "auto")

        self.assertEqual(doi_key, ("doi", "10.1000/xyz"))
        self.assertEqual(url_key, ("url", "https://example.com/path/to/paper"))
        self.assertEqual(title_key, ("title", "neural policy for mobile robot|2022"))

    def test_canonical_group_key_modes(self) -> None:
        data = self.fx["doi_case"]
        self.assertEqual(merge.canonical_group_key(data, "doi"), ("doi", "10.1000/xyz"))
        self.assertEqual(merge.canonical_group_key(data, "url"), ("url", "https://example.com/paper"))
        self.assertEqual(merge.canonical_group_key(data, "title"), ("title", "a great paper|2024"))

    def test_dedupe_children_with_fixture(self) -> None:
        existing = self.fx["existing_children"]
        incoming = self.fx["incoming_children"]
        unique = merge.dedupe_children(existing, incoming)
        self.assertEqual(len(unique), 1)
        self.assertEqual(unique[0]["key"], "A3")

    def test_has_pdf_attachment(self) -> None:
        self.assertTrue(merge.has_pdf_attachment(self.fx["existing_children"]))
        no_pdf = [
            {"key": "A4", "data": {"itemType": "attachment", "filename": "notes.txt", "contentType": "text/plain"}}
        ]
        self.assertFalse(merge.has_pdf_attachment(no_pdf))


if __name__ == "__main__":
    unittest.main()
