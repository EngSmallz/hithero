import { defineConfig } from '@playwright/test';

export default defineConfig({
	use: { baseURL: 'http://localhost:4173' },
	webServer: [
		{
			command:
				'python -c "import app; app.init_db()" && python -m uvicorn app:app --host 127.0.0.1 --port 8001',
			cwd: '..',
			port: 8001,
			env: {
				APP_ENV: 'test',
				CORS_ALLOW_ORIGINS: 'http://localhost:4173',
				SECRET_KEY: 'test-secret',
				TEST_DATABASE_URL: 'sqlite:///./.tmp/hithero-playwright.sqlite',
				PYTHONPATH: 'tests/stubs'
			},
			reuseExistingServer: false
		},
		{
			command: 'npm run build && npm run preview',
			port: 4173,
			env: { PUBLIC_BACKEND_ORIGIN: 'http://localhost:8001' }
		}
	],
	testMatch: '**/*.e2e.{ts,js}'
});
