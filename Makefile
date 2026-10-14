PY = .venv/bin/python
.PHONY: setup test run report
setup:
	python3 -m venv .venv
	$(PY) -m pip install -r requirements.txt
test:
	$(PY) -m pytest tests -q
run:
	$(PY) src/experiment.py
	$(PY) src/decision_memo.py
	$(PY) src/summary_html.py
report:
	open resultados/RESUMO_ATUAL.html
