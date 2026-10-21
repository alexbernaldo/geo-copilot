PY := .venv/bin/python

install:
	python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
	cd frontend && npm ci

# Desarrollo: backend (8000) + Vite (5173) con proxy de /api
dev:
	$(PY) -m uvicorn backend.main:app --reload --port 8000 & cd frontend && npm run dev

build:
	cd frontend && npm run build

# Producción local: un solo proceso y puerto; abre el navegador
app:
	$(PY) scripts/geo_copilot.py

test:
	$(PY) -m pytest -q
	cd frontend && npm run typecheck && npm test

e2e:
	cd frontend && npx playwright test --config ../e2e/playwright.config.ts

fingerprints:
	$(PY) scripts/compute_reference_fingerprints.py

fixtures:
	$(PY) scripts/dump_api_fixtures.py

fake-or:
	$(PY) scripts/fake_openrouter.py --port 8765

# H6: detector de anti-patrones de Impeccable sobre el código y sobre cada ruta (con el servidor de desarrollo levantado)
design-check:
	npx impeccable detect frontend/src --json > coord/reviews/detect_src.json
	while read r; do npx impeccable detect "http://localhost:$${PORT:-5173}$$r" || exit $$?; done < frontend/design-routes.txt

.PHONY: install dev build app test e2e fingerprints fixtures fake-or design-check
