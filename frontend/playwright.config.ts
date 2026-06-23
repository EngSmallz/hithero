import { defineConfig } from '@playwright/test';

const backendPort = Number(process.env.PLAYWRIGHT_BACKEND_PORT ?? 8001);
const frontendPort = Number(process.env.PLAYWRIGHT_FRONTEND_PORT ?? 4173);
const backendOrigin = `http://localhost:${backendPort}`;
const frontendOrigin = `http://localhost:${frontendPort}`;
const databaseSuffix =
	process.env.TEST_WORKER_INDEX ?? process.env.PLAYWRIGHT_WORKER_INDEX ?? 'main';
const parseWorkers = (value: string | undefined, fallback: number | string) =>
	value ? (value.endsWith('%') ? value : Number(value)) : fallback;
const frontendCommand = process.env.PLAYWRIGHT_SKIP_BUILD
	? 'npm run preview'
	: 'npm run build && npm run preview';

export default defineConfig({
	fullyParallel: true,
	workers: parseWorkers(process.env.PLAYWRIGHT_WORKERS, '50%'),
	use: { baseURL: frontendOrigin },
	webServer: [
		{
			command: `python -c "import app; app.init_db()" && python -m uvicorn app:app --host 127.0.0.1 --port ${backendPort}`,
			cwd: '..',
			port: backendPort,
			env: {
				APP_ENV: 'test',
				CORS_ALLOW_ORIGINS: frontendOrigin,
				SECRET_KEY: 'test-secret',
				TEST_DATABASE_URL: `sqlite:///./.tmp/hithero-playwright-${databaseSuffix}.sqlite`,
				PYTHONPATH: 'tests/stubs'
			},
			reuseExistingServer: false
		},
		{
			command: frontendCommand,
			port: frontendPort,
			env: { PUBLIC_BACKEND_ORIGIN: backendOrigin }
		}
	],
	testMatch: '**/*.e2e.{ts,js}'
});
