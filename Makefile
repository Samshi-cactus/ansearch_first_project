# -------- Settings --------
VENV ?= .venv
PY    := $(VENV)/bin/python
PIP   := $(VENV)/bin/pip
RUFF  := $(VENV)/bin/ruff
BLACK := $(VENV)/bin/black
PYLINT:= $(VENV)/bin/pylint
PYTEST:= $(VENV)/bin/pytest

SRC     := src
SCRIPTS := scripts
TESTS   := tests

# Optional: load .env so PYTHONPATH=.
ENV := set -a; [ -f .env ] && . .env || true; set +a;

.PHONY: venv deps fmt lint test names topics summary clean all

# Create venv
venv:
	python -m venv $(VENV)

# Install deps (inc. spaCy model)
deps: venv
	$(ENV) $(PIP) install -U pip
	$(ENV) $(PIP) install -r requirements.txt
	# optional – improves name resolution but not required for core pipeline
	-$(ENV) $(PY) -m spacy download en_core_web_sm


# Run tests
test:
	$(ENV) PYTHONWARNINGS="ignore:Importing 'parser.split_arg_string' is deprecated:DeprecationWarning" \
	$(PYTEST) -q

# Suggest names for all JSONL files in data/
names:
	$(ENV) $(PY) scripts/resolve_place_names.py data/*.jsonl

# Run topic extraction batch
topics:
	$(ENV) bash scripts/run_all_topics.sh

# Summarise outputs to CSV
summary:
	$(ENV) $(PY) scripts/summarize_outputs.py


# One-click local CI
all: deps test topics summary
