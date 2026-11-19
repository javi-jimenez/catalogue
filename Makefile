# brisecom-catalogue — metadatos de BRISECOM como JSON.
# La fuente de verdad son los JSON; el vault es una vista generada.

PYTHON ?= python3

.PHONY: help
help:
	@echo "brisecom-catalogue"
	@echo
	@echo "  make validate   valida JSON, referencias cruzadas y precios"
	@echo "  make vault      regenera vault/ (notas Markdown para Obsidian)"
	@echo "  make site       genera docs/ (sitio de metadatos para GitHub Pages)"
	@echo "  make lint       valida el JSON-LD de fuentes y del sitio"
	@echo "  make check      validate + lint + vault + site al día (para CI)"
	@echo "  make all        validate + vault + site"

.PHONY: validate
validate:
	@$(PYTHON) validate.py

.PHONY: vault
vault:
	@$(PYTHON) scripts/vault_export.py

.PHONY: site
site:
	@$(PYTHON) scripts/build_site.py

.PHONY: lint
lint:
	@$(PYTHON) scripts/lint_jsonld.py

.PHONY: check
check:
	@$(PYTHON) validate.py
	@$(PYTHON) scripts/lint_jsonld.py
	@$(PYTHON) scripts/vault_export.py --check
	@$(PYTHON) scripts/build_site.py --check

.PHONY: all
all: validate vault site
