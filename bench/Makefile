# Benchmark harness for README_AI.md agent comprehension experiments.
#
# This is the tooling that produced the data backing ADR-005.
# It is NOT shipped to end users — only useful for codeindex maintainers
# validating prompt/format changes against agent behavior.
#
# Workflow:
#   1. `make setup`          — copy example configs you must edit
#   2. (edit targets.yaml + questions.yaml)
#   3. `make scan`           — scan each target project (sanity check)
#   4. `make run`            — 30 sonnet calls × your projects/questions
#   5. `make grade`          — LLM-as-judge with haiku, writes _graded.csv
#   6. `make report`         — print headline comparison table
#
# Requirements: `claude` CLI on PATH, ANTHROPIC_API_KEY available,
# python3 + pyyaml. Burns roughly $3-7 per full benchmark depending on
# question count and project size.

PYTHON ?= python3
QUESTIONS ?= questions.yaml
OUTPUT ?= results.csv
VARIANTS ?= wo,disclaimer
TARGETS ?= targets.yaml
PARALLEL ?= 12

.PHONY: help setup scan run run-resume grade report clean clean-all

help:
	@echo "Targets:"
	@echo "  setup       Copy example yaml templates so you can edit local copies"
	@echo "  scan        Re-scan every target project with codeindex (haiku, --retry-all)"
	@echo "  run         Run benchmark (VARIANTS=wo,disclaimer by default)"
	@echo "  run-resume  Same as 'run' but --skip-existing (resume after rate-limit hit)"
	@echo "  grade       LLM-as-judge grade $(OUTPUT) → $(OUTPUT:.csv=_graded.csv)"
	@echo "  report      Print headline table from graded CSV"
	@echo "  clean       Remove logs + results from this run"
	@echo "  clean-all   Also remove copied yaml configs (irreversible — careful)"
	@echo ""
	@echo "Override defaults via env: QUESTIONS=, OUTPUT=, VARIANTS=, TARGETS=, PARALLEL="

setup:
	@test -f targets.yaml   || (cp targets.yaml.example targets.yaml      && echo "✓ targets.yaml created — edit project paths")
	@test -f questions.yaml || (cp questions.yaml.example questions.yaml  && echo "✓ questions.yaml created — fill in questions + ref_answers")
	@test -f .env.example   && (test -f .env || cp .env.example .env)     || true

scan:
	@$(PYTHON) -c "import yaml,subprocess,sys; \
cfg=yaml.safe_load(open('$(TARGETS)')); \
[subprocess.run(['codeindex','scan-all','--ai','--retry-all','-p','$(PARALLEL)'], cwd=p['path'], check=True) for p in cfg['targets']]"

run:
	$(PYTHON) run_bench.py --questions $(QUESTIONS) --output $(OUTPUT) --variants $(VARIANTS)

run-resume:
	$(PYTHON) run_bench.py --questions $(QUESTIONS) --output $(OUTPUT) --variants $(VARIANTS) --skip-existing

grade:
	$(PYTHON) grade.py --input $(OUTPUT) --output $(OUTPUT:.csv=_graded.csv)

report:
	@$(PYTHON) report.py $(OUTPUT:.csv=_graded.csv)

clean:
	rm -f *.log results*.csv results*_graded.csv

clean-all: clean
	rm -f targets.yaml questions.yaml .env
