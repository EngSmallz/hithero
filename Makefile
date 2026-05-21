.PHONY: install-dev test-static test-e2e test

install-dev:
	python -m pip install -r requirements.txt -r requirements-dev.txt
	python -m playwright install chromium

test-static:
	APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests --ignore=tests/e2e

test-e2e:
	APP_ENV=test SECRET_KEY=test-secret PYTHONPATH=tests/stubs PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/e2e

test: test-static test-e2e
