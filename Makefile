PUBLIC_BACKEND_ORIGIN ?= http://localhost:8000
DEV_DATABASE_URL ?= sqlite:///./.local/hithero-dev.sqlite
TEST_DATABASE_URL ?= sqlite:///./.tmp/hithero-test.sqlite
PYTEST_WORKERS ?= auto
PYTEST_E2E_WORKERS ?= 2
FRONTEND_NPM ?= npm --prefix frontend

.PHONY: install-dev dev-backend dev-frontend init-test-db test-static test-static-db test-e2e test-forum-api test-teachers-api test-frontend-integration-one test

install-dev:
	python -m pip install -r requirements.txt -r requirements-dev.txt
	python -m playwright install chromium

dev-backend:
	APP_ENV=development SECRET_KEY=$${SECRET_KEY:-dev-secret} DATABASE_URL=$(DEV_DATABASE_URL) uvicorn app:app --reload --host 127.0.0.1 --port 8000

dev-frontend:
	cd frontend && PUBLIC_BACKEND_ORIGIN=$(PUBLIC_BACKEND_ORIGIN) npm run dev -- --host 127.0.0.1

init-test-db:
	APP_ENV=test SECRET_KEY=test-secret TEST_DATABASE_URL=$(TEST_DATABASE_URL) python -c "import app; app.init_db(); print(f'Initialized {app.SQLALCHEMY_DATABASE_URL}')"

test-static:
	APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -p xdist -n $(PYTEST_WORKERS) tests --ignore=tests/e2e

test-static-db:
	APP_ENV=test SECRET_KEY=test-secret TEST_DATABASE_URL=$(TEST_DATABASE_URL) PYTHONPATH=tests/stubs PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -p xdist -n $(PYTEST_WORKERS) tests --ignore=tests/e2e

test-e2e:
	APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -p xdist -n $(PYTEST_E2E_WORKERS) tests/e2e

test-forum-api:
	APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/test_forum_formatting.py tests/test_forum_session_cleanup.py

test-teachers-api:
	APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/test_teacher_directory_api.py

test-frontend-integration-one:
	INTEGRATION_WORKERS=1 $(FRONTEND_NPM) run test:integration

test: test-static test-e2e
