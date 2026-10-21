install:
	python -m venv .venv && .venv/bin/pip install -r requirements.txt

test:
	.venv/bin/python -m pytest -q

app:
	.venv/bin/python scripts/geo_copilot.py

demo:
	.venv/bin/python -c "import os; os.environ['LLM_PROVIDER']='mock'; from geo.orchestrator import Run; from geo.config import BRIEF_MD; Run(run_id='demo', modo='cliente', brief_path=BRIEF_MD, provider='mock').run_all(auto_approve=True)"

fake-or:
	.venv/bin/python scripts/fake_openrouter.py --port 8765
