.PHONY: analysis-venv test

# Optional Python environment for analyzing attached experimental data. Kept
# separate from the project .venv so the heavy sci stack is opt-in. Regenerable;
# gitignored.
ANALYSIS_VENV := .analysis-venv

analysis-venv:
	uv venv $(ANALYSIS_VENV) --python 3.12
	VIRTUAL_ENV=$(ANALYSIS_VENV) uv pip install pandas numpy scipy matplotlib
	$(ANALYSIS_VENV)/bin/python -c "import pandas, numpy, scipy, matplotlib; print('analysis venv ok:', pandas.__version__)"

test:
	.venv/bin/pytest
