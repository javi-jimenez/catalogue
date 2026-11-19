# brisecom-catalogue — metadatos de BRISECOM como JSON.
# La fuente de verdad son los JSON; el vault es una vista generada.

PYTHON ?= python3

.PHONY: help
help:
	@echo "brisecom-catalogue"
	@echo
	@echo "  make validate   valida JSON, referencias cruzadas y precios"
	@echo "  make vault      regenera vault/ (notas Markdown para Obsidian)"
	@echo "  make check      validate + vault al día (para CI)"
	@echo "  make all        validate + vault"

.PHONY: validate
validate:
	@$(PYTHON) validate.py

.PHONY: vault
vault:
	@$(PYTHON) scripts/vault_export.py

.PHONY: check
check:
	@$(PYTHON) validate.py
	@$(PYTHON) scripts/vault_export.py --check

.PHONY: all
all: validate vault
