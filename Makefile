PY=python

.PHONY: setup build llm quality clean

setup:
	python -m pip install --upgrade pip
	pip install -r commentary/requirements.txt
	bash commentary/scripts/install_llama.sh
	@echo ">>> Place your GGUF at commentary/models/model.gguf when ready."

build:
	$(PY) commentary/render.py
	$(PY) commentary/quality.py
	@echo "✅ Built commentary/out/monthly_commentary.md and dashboard.xlsx"

llm:
	$(PY) commentary/render.py
	@echo "✅ LLM-polished commentary ready."

quality:
	$(PY) commentary/quality.py

clean:
	rm -rf commentary/out