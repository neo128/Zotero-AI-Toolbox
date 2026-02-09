import pathlib
import subprocess
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PYTHON = sys.executable


class DocsCommandSmokeTest(unittest.TestCase):
    def _run(self, command, expect: str = "usage") -> None:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=f"Failed: {' '.join(command)}\n{proc.stdout}")
        self.assertIn(expect, proc.stdout.lower(), msg=proc.stdout)

    def _assert_contains(self, path: pathlib.Path, snippet: str) -> None:
        text = path.read_text(encoding="utf-8")
        self.assertIn(snippet, text, msg=f"Snippet not found in {path}: {snippet}")

    def test_readme_quickstart_commands(self) -> None:
        readmes = [ROOT / "README.md", ROOT / "README_EN.md"]
        snippet_a = "python scripts/langchain_pipeline.py --help"
        snippet_b = "scripts/ai_toolbox_pipeline.sh --help"

        for doc in readmes:
            with self.subTest(doc=doc, snippet=snippet_a):
                self._assert_contains(doc, snippet_a)
            with self.subTest(doc=doc, snippet=snippet_b):
                self._assert_contains(doc, snippet_b)

        self._run([PYTHON, "scripts/langchain_pipeline.py", "--help"])
        self._run(["bash", "scripts/ai_toolbox_pipeline.sh", "--help"])

    def test_release_guide_snippets_exist(self) -> None:
        release_doc = ROOT / "docs" / "RELEASE.md"
        self.assertTrue(release_doc.exists(), msg=f"Missing file: {release_doc}")
        self._assert_contains(release_doc, "make ci")
        self._assert_contains(release_doc, "git tag v0.1.1")
        self._assert_contains(release_doc, "git push origin v0.1.1")


if __name__ == "__main__":
    unittest.main()
