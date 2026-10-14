PY ?= .venv/bin/python
.PHONY: setup test analyze notebook
setup:
	python3 -m venv .venv
	$(PY) -m pip install -r requirements.txt
test:
	$(PY) -m pytest tests -q
analyze:
	$(PY) src/experiment.py
notebook:
	$(PY) -m jupyterlab notebooks/analise_experimento.ipynb
