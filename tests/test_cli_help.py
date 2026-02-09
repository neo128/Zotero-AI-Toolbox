import pathlib
import subprocess
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PYTHON = sys.executable


class CliHelpTest(unittest.TestCase):
    def _run(self, cmd):
        completed = subprocess.run(
            cmd,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            msg=f"Command failed: {' '.join(cmd)}\n{completed.stdout}",
        )
        self.assertIn("usage", completed.stdout.lower(), msg=completed.stdout)

    def test_python_cli_help(self):
        scripts = [
            "scripts/list_zotero_collections.py",
            "scripts/merge_zotero_duplicates.py",
            "scripts/watch_and_import_papers.py",
            "scripts/fetch_missing_pdfs.py",
            "scripts/summarize_zotero_with_doubao.py",
            "scripts/enrich_zotero_abstracts.py",
            "scripts/sync_zotero_to_notion.py",
            "scripts/langchain_pipeline.py",
        ]
        for script in scripts:
            with self.subTest(script=script):
                self._run([PYTHON, script, "--help"])

    def test_shell_pipeline_help(self):
        self._run(["bash", "scripts/ai_toolbox_pipeline.sh", "--help"])


if __name__ == "__main__":
    unittest.main()
