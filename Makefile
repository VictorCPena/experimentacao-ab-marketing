PY ?= .venv/bin/python
.PHONY: simulate simulate-smoke setup test analyze notebook sensitivity
setup:
	python3 -m venv .venv
	$(PY) -m pip install -r requirements.txt
test:
	$(PY) -m pytest tests -q
analyze:
	$(PY) src/experiment.py
notebook:
	$(PY) -m jupyterlab notebooks/analise_experimento.ipynb

sensitivity:
	$(PY) src/sensitivity.py

simulate:
	$(PY) src/design_simulation.py

simulate-smoke:
	$(PY) src/design_simulation.py --reps 300 --per-arm 500

advanced-design:
	$(PY) src/advanced_design.py --reps 300 --clusters 25 --size 25

advanced-smoke:
	$(PY) src/advanced_design.py --reps 100 --clusters 12 --size 10
