import { defineConfig } from '@playwright/test';

const parseWorkers = (value: string | undefined, fallback: number | string) =>
	value ? (value.endsWith('%') ? value : Number(value)) : fallback;

export default defineConfig({
	testDir: 'tests/integration',
	testMatch: '**/*.integration.ts',
	fullyParallel: true,
	workers: parseWorkers(process.env.INTEGRATION_WORKERS, 2),
	timeout: 60_000,
	expect: {
		timeout: 10_000
	}
});
