import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def iter_local_links(md_path: pathlib.Path):
    text = md_path.read_text(encoding="utf-8")
    for raw in LINK_RE.findall(text):
        link = raw.strip()
        if not link:
            continue
        if link.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = link.split("#", 1)[0]
        if not target:
            continue
        yield target


class MarkdownLinkTest(unittest.TestCase):
    def test_local_links_exist(self) -> None:
        files = [
            ROOT / "README.md",
            ROOT / "README_EN.md",
            ROOT / "CONTRIBUTING.md",
            ROOT / "SUPPORT.md",
            ROOT / "ROADMAP.md",
            ROOT / "docs" / "USE_CASES.md",
            ROOT / "docs" / "BEFORE_AFTER.md",
            ROOT / "docs" / "RELEASE.md",
            ROOT / "docs" / "TROUBLESHOOTING.md",
        ]
        for md in files:
            self.assertTrue(md.exists(), msg=f"Missing markdown file: {md}")
            for link in iter_local_links(md):
                target = (md.parent / link).resolve()
                with self.subTest(markdown=str(md), link=link):
                    self.assertTrue(target.exists(), msg=f"Broken link '{link}' in {md}")


if __name__ == "__main__":
    unittest.main()
