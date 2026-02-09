import copy
import json
import pathlib
import sys
import unittest
from unittest.mock import patch


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import enrich_zotero_abstracts as enrich  # noqa: E402


FIXTURE_PATH = ROOT / "tests" / "fixtures" / "enrich_abstract_fixture.json"


class EnrichAbstractLogicTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fx = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_clean_doi_and_extract_arxiv_id(self) -> None:
        self.assertEqual(enrich.clean_doi("https://doi.org/10.1000/xyz"), "10.1000/xyz")
        self.assertEqual(enrich.clean_doi("doi:10.1000/abc"), "10.1000/abc")
        self.assertEqual(enrich.extract_arxiv_id("https://arxiv.org/abs/2401.12345"), "2401.12345")
        self.assertEqual(enrich.extract_arxiv_id("arxiv:2401.54321"), "2401.54321")

    def test_has_abstract(self) -> None:
        with_abs = copy.deepcopy(self.fx["entry_with_abstract"]["data"])
        no_abs = copy.deepcopy(self.fx["entry_with_doi_and_arxiv"]["data"])
        self.assertTrue(enrich.has_abstract(with_abs))
        self.assertFalse(enrich.has_abstract(no_abs))

    @patch.object(enrich, "fetch_arxiv_abstract")
    @patch.object(enrich, "fetch_semantic_scholar_abstract")
    @patch.object(enrich, "fetch_crossref_abstract")
    @patch.object(enrich, "fetch_url_abstract")
    def test_enrich_item_prefers_url_result(
        self,
        m_url,
        m_crossref,
        m_semantic,
        m_arxiv,
    ) -> None:
        entry = copy.deepcopy(self.fx["entry_with_doi_and_arxiv"])
        m_url.return_value = {"source": "URL meta", "text": "from-url"}

        result = enrich.enrich_item(entry)

        self.assertEqual(result, {"source": "URL meta", "text": "from-url"})
        m_crossref.assert_not_called()
        m_semantic.assert_not_called()
        m_arxiv.assert_not_called()

    @patch.object(enrich, "fetch_arxiv_abstract")
    @patch.object(enrich, "fetch_semantic_scholar_abstract")
    @patch.object(enrich, "fetch_crossref_abstract")
    @patch.object(enrich, "fetch_url_abstract")
    def test_enrich_item_semantic_rate_limit_falls_back_to_arxiv(
        self,
        m_url,
        m_crossref,
        m_semantic,
        m_arxiv,
    ) -> None:
        entry = copy.deepcopy(self.fx["entry_with_doi_and_arxiv"])
        m_url.return_value = None
        m_crossref.return_value = None
        m_semantic.return_value = "RATE_LIMIT"
        m_arxiv.return_value = "from-arxiv"

        result = enrich.enrich_item(entry)

        self.assertEqual(result, {"source": "arXiv", "text": "from-arxiv"})
        m_semantic.assert_called_once_with("DOI", "10.1000/xyz")
        m_arxiv.assert_called_once_with("2401.12345")


if __name__ == "__main__":
    unittest.main()
