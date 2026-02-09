import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY_RE = re.compile(r"^([A-Z0-9_]+)\s*=")


def parse_keys(path: pathlib.Path) -> set[str]:
    keys: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = KEY_RE.match(line)
        if match:
            keys.add(match.group(1))
    return keys


class EnvTemplateTest(unittest.TestCase):
    def test_zotero_template_keys(self) -> None:
        template = ROOT / ".env.zotero.example"
        self.assertTrue(template.exists(), msg=f"Missing template: {template}")
        keys = parse_keys(template)
        required = {"ZOTERO_USER_ID", "ZOTERO_API_KEY"}
        self.assertTrue(required.issubset(keys), msg=f"Missing keys: {required - keys}")

    def test_zotero_notion_template_keys(self) -> None:
        template = ROOT / ".env.zotero_notion.example"
        self.assertTrue(template.exists(), msg=f"Missing template: {template}")
        keys = parse_keys(template)
        required = {"ZOTERO_USER_ID", "ZOTERO_API_KEY", "NOTION_TOKEN", "NOTION_DATABASE_ID"}
        self.assertTrue(required.issubset(keys), msg=f"Missing keys: {required - keys}")


if __name__ == "__main__":
    unittest.main()
