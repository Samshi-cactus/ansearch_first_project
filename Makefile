                                              # -------- Settings --------
VENV ?= .venv
PY    := $(VENV)/bin/python
PIP   := $(VENV)/bin/pip
SRC   := src
SCRIPTS := scripts
TESTS := tests

.PHONY: deps test topics summary clean

# Create venv + install deps
deps:
	python -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt
	$(PY) -m spacy download en_core_web_sm

# Run tests
test:
	. .venv/bin/activate && \
	PYTHONWARNINGS="ignore" pytest -q

# Extract topics for all restaurants
topics:
	bash scripts/run_all_topics.sh

# Summarise outputs
summary:
	$(PY) scripts/summarize_outputs.py

clean:
	rm -rf $(VENV) .pytest_cache .ruff_cache
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
