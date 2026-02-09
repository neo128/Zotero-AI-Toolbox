PYTHON ?= python

.PHONY: help install check test ci

help:
	@echo "Common targets:"
	@echo "  make install   Install runtime dependencies"
	@echo "  make check     Run syntax and CLI smoke checks"
	@echo "  make test      Run unit tests"
	@echo "  make ci        Run check + test"

install:
	$(PYTHON) -m pip install -r requirements.txt

check:
	$(PYTHON) -m compileall scripts paperflow tests
	bash -n scripts/ai_toolbox_pipeline.sh
	$(PYTHON) scripts/list_zotero_collections.py --help >/dev/null
	$(PYTHON) scripts/merge_zotero_duplicates.py --help >/dev/null
	$(PYTHON) scripts/watch_and_import_papers.py --help >/dev/null
	$(PYTHON) scripts/fetch_missing_pdfs.py --help >/dev/null
	$(PYTHON) scripts/summarize_zotero_with_doubao.py --help >/dev/null
	$(PYTHON) scripts/enrich_zotero_abstracts.py --help >/dev/null
	$(PYTHON) scripts/sync_zotero_to_notion.py --help >/dev/null
	$(PYTHON) scripts/langchain_pipeline.py --help >/dev/null
	bash scripts/ai_toolbox_pipeline.sh --help >/dev/null

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py" -v

ci: check test
