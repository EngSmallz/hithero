import { expect, test, type Page, type Response as PlaywrightResponse } from '@playwright/test';
import { execFile } from 'node:child_process';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, resolve } from 'node:path';
import { type Readable } from 'node:stream';
import { fileURLToPath } from 'node:url';
import net from 'node:net';
import { spawn, type ChildProcessByStdio, type SpawnOptionsWithoutStdio } from 'node:child_process';

const TEST_RECAPTCHA_TOKEN = 'hithero-test-recaptcha';
const __filename = fileURLToPath(import.meta.url);
const integrationDir = dirname(__filename);
const frontendDir = resolve(integrationDir, '../..');
const rootDir = resolve(frontendDir, '..');
const dbHelperPath = resolve(integrationDir, 'db_helper.py');

type TestStack = {
	backendOrigin: string;
	frontendOrigin: string;
	dbDir: string;
	env: NodeJS.ProcessEnv;
	backend: ManagedProcess;
	frontend: ManagedProcess;
};

type NewUserRecord = {
	email: string;
	name: string;
	phone_number: string;
	state: string;
	county: string;
	district: string;
	school: string;
	role: string;
	report: number;
	emailed: number;
	password_is_hashed: boolean;
};

class ManagedProcess {
	readonly child: ChildProcessByStdio<null, Readable, Readable>;
	private output = '';

	constructor(
		private readonly label: string,
		command: string,
		args: string[],
		options: SpawnOptionsWithoutStdio
	) {
		this.child = spawn(command, args, { ...options, stdio: ['ignore', 'pipe', 'pipe'] });
		this.child.stdout.on('data', (chunk: Buffer) => this.capture(chunk));
		this.child.stderr.on('data', (chunk: Buffer) => this.capture(chunk));
	}

	logs(): string {
		return `[${this.label}]\n${this.output}`;
	}

	async stop(): Promise<void> {
		if (this.child.exitCode !== null || this.child.signalCode !== null) {
			return;
		}

		const exited = new Promise<void>((resolveExited) => {
			this.child.once('exit', () => resolveExited());
		});
		this.child.kill('SIGTERM');

		await Promise.race([
			exited,
			delay(5_000).then(() => {
				if (this.child.exitCode === null && this.child.signalCode === null) {
					this.child.kill('SIGKILL');
				}
			})
		]);
	}

	private capture(chunk: Buffer): void {
		this.output = `${this.output}${chunk.toString()}`;
		if (this.output.length > 20_000) {
			this.output = this.output.slice(-20_000);
		}
	}
}

let stack: TestStack;

test.describe.configure({ mode: 'serial' });

test.beforeAll(async () => {
	stack = await startStack();
});

test.afterAll(async () => {
	if (!stack) {
		return;
	}

	await Promise.all([stack.frontend.stop(), stack.backend.stop()]);
	await rm(stack.dbDir, { recursive: true, force: true });
});

test('teacher login posts to FastAPI and redirects teachers without a profile', async ({
	page,
	context
}) => {
	await resetDatabase();
	await seedLoginUser({
		email: 'teacher.integration@example.test',
		password: 'correct horse battery staple',
		createCount: 0
	});

	await gotoFrontend(page, '/login');
	await page.getByLabel(/^Email/).fill('teacher.integration@example.test');
	await page.getByLabel(/^Password/).fill('correct horse battery staple');

	const loginResponse = await submitAndWaitForBackendPost(
		page,
		() => page.getByRole('button', { name: 'Submit' }).click(),
		'/profile/login/'
	);

	expect(loginResponse.status()).toBe(200);
	await expect.poll(() => new URL(page.url()).pathname).toBe('/profile/create');
	expect(new URL(page.url()).origin).toBe(stack.backendOrigin);

	const cookies = await context.cookies(stack.backendOrigin);
	const sessionCookie = cookies.find((cookie) => cookie.name === 'session');
	expect(sessionCookie?.value).toBeTruthy();
});

test('wrong password posts to FastAPI and stays on login with invalid credential message', async ({
	page
}) => {
	await resetDatabase();
	await seedLoginUser({
		email: 'teacher.integration@example.test',
		password: 'correct horse battery staple',
		createCount: 0
	});

	await gotoFrontend(page, '/login');
	await page.getByLabel(/^Email/).fill('teacher.integration@example.test');
	await page.getByLabel(/^Password/).fill('wrong-password');

	const loginResponse = await submitAndWaitForBackendPost(
		page,
		() => page.getByRole('button', { name: 'Submit' }).click(),
		'/profile/login/'
	);

	expect(loginResponse.status()).toBe(200);
	await expect(page).toHaveURL(`${stack.frontendOrigin}/login`);
	await expect(page.getByRole('status')).toContainText('Invalid login credentials.');
});

test('registration posts to FastAPI and queues a NewUsers validation row', async ({ page }) => {
	await resetDatabase();
	await seedSchool({
		state: 'Integration State',
		county: 'Integration County',
		district: 'Integration District',
		school: 'Integration Elementary'
	});
	await installRecaptchaStub(page);

	const email = 'new.teacher.integration@example.test';
	const password = 'registration password';

	await gotoFrontend(page, '/register');
	await expect(page.getByLabel(/^State/)).toContainText('Integration State');

	await page.getByLabel(/^Name/).fill('Integration Teacher');
	await page.getByLabel(/^Email/).fill(email);
	await page.getByLabel(/^Phone Number/).fill('555-0199');
	await page.getByLabel(/^Password/).fill(password);
	await page.getByLabel(/^Confirm Password/).fill(password);
	await page.getByLabel(/^State/).selectOption('Integration State');
	await expect(page.getByLabel(/^County/)).toContainText('Integration County');
	await page.getByLabel(/^County/).selectOption('Integration County');
	await expect(page.getByLabel(/^School District/)).toContainText('Integration District');
	await page.getByLabel(/^School District/).selectOption('Integration District');
	await expect(page.getByLabel(/^School required$/)).toContainText('Integration Elementary');
	await page.getByLabel(/^School required$/).selectOption('Integration Elementary');
	await page.getByLabel('I have read the Terms and Conditions').check();

	const registerResponse = await submitAndWaitForBackendPost(
		page,
		() => page.getByRole('button', { name: 'Submit' }).click(),
		'/profile/register/'
	);

	expect(registerResponse.status()).toBe(200);
	await expect(page.getByRole('status')).toContainText('User registered successfully');

	const newUser = await getNewUser(email, password);
	expect(newUser).toMatchObject({
		email,
		name: 'Integration Teacher',
		phone_number: '555-0199',
		state: 'Integration State',
		county: 'Integration County',
		district: 'Integration District',
		school: 'Integration Elementary',
		role: 'teacher',
		report: 0,
		emailed: 0,
		password_is_hashed: true
	});
});

async function startStack(): Promise<TestStack> {
	const backendPort = await getFreePort();
	const frontendPort = await getFreePort();
	const backendOrigin = `http://127.0.0.1:${backendPort}`;
	const frontendOrigin = `http://127.0.0.1:${frontendPort}`;
	const dbDir = await mkdtemp(resolve(tmpdir(), 'hithero-integration-'));
	const dbPath = resolve(dbDir, 'hithero.sqlite');
	const env = {
		...process.env,
		APP_ENV: 'test',
		SECRET_KEY: 'integration-test-secret',
		TEST_DATABASE_URL: `sqlite:///${dbPath}`,
		TEST_RECAPTCHA_TOKEN,
		CORS_ALLOW_ORIGINS: frontendOrigin
	};

	await runDbHelper(['reset'], env);

	let backend: ManagedProcess | undefined;
	let frontend: ManagedProcess | undefined;

	try {
		backend = new ManagedProcess(
			'FastAPI',
			'python',
			['-m', 'uvicorn', 'app:app', '--host', '127.0.0.1', '--port', String(backendPort)],
			{ cwd: rootDir, env }
		);
		await waitForHttp(`${backendOrigin}/api/get_states/`, backend);

		frontend = new ManagedProcess(
			'SvelteKit',
			'npm',
			['run', 'dev', '--', '--host', '127.0.0.1', '--port', String(frontendPort), '--strictPort'],
			{
				cwd: frontendDir,
				env: {
					...env,
					PUBLIC_BACKEND_ORIGIN: backendOrigin
				}
			}
		);
		await waitForHttp(`${frontendOrigin}/login`, frontend);

		return {
			backendOrigin,
			frontendOrigin,
			dbDir,
			env,
			backend,
			frontend
		};
	} catch (error) {
		await Promise.all([frontend?.stop(), backend?.stop()]);
		await rm(dbDir, { recursive: true, force: true });
		throw error;
	}
}

async function resetDatabase(): Promise<void> {
	await runDbHelper(['reset'], stack.env);
}

async function seedLoginUser(args: {
	email: string;
	password: string;
	createCount: number;
}): Promise<void> {
	await runDbHelper(
		[
			'seed-login-user',
			'--email',
			args.email,
			'--password',
			args.password,
			'--role',
			'teacher',
			'--create-count',
			String(args.createCount)
		],
		stack.env
	);
}

async function seedSchool(args: {
	state: string;
	county: string;
	district: string;
	school: string;
}): Promise<void> {
	await runDbHelper(
		[
			'seed-school',
			'--state',
			args.state,
			'--county',
			args.county,
			'--district',
			args.district,
			'--school',
			args.school
		],
		stack.env
	);
}

async function getNewUser(email: string, plainPassword: string): Promise<NewUserRecord> {
	const output = await runDbHelper(
		['get-new-user', '--email', email, '--plain-password', plainPassword],
		stack.env
	);
	const record = JSON.parse(output) as NewUserRecord | null;

	expect(record).not.toBeNull();
	return record as NewUserRecord;
}

async function submitAndWaitForBackendPost(
	page: Page,
	action: () => Promise<void>,
	path: '/profile/login/' | '/profile/register/'
): Promise<PlaywrightResponse> {
	const responsePromise = page.waitForResponse(
		(response) =>
			response.url() === `${stack.backendOrigin}${path}` && response.request().method() === 'POST'
	);
	await action();
	return responsePromise;
}

async function gotoFrontend(page: Page, path: '/login' | '/register'): Promise<void> {
	await page.goto(`${stack.frontendOrigin}${path}`, { waitUntil: 'load' });
	await page.waitForLoadState('networkidle');
}

async function installRecaptchaStub(page: Page): Promise<void> {
	await page.route('https://www.google.com/recaptcha/**', async (route) => {
		await route.fulfill({
			contentType: 'application/javascript',
			body: `window.grecaptcha = { getResponse: () => '${TEST_RECAPTCHA_TOKEN}', reset: () => {} };`
		});
	});
	await page.addInitScript((token: string) => {
		(
			window as Window & {
				grecaptcha?: { getResponse: () => string; reset: () => void };
			}
		).grecaptcha = {
			getResponse: () => token,
			reset: () => {}
		};
	}, TEST_RECAPTCHA_TOKEN);
}

async function runDbHelper(args: string[], env: NodeJS.ProcessEnv): Promise<string> {
	return new Promise((resolveOutput, rejectOutput) => {
		execFile('python', [dbHelperPath, ...args], { cwd: rootDir, env }, (error, stdout, stderr) => {
			if (error) {
				rejectOutput(
					new Error(`DB helper failed: python ${dbHelperPath} ${args.join(' ')}\n${stderr}`)
				);
				return;
			}

			resolveOutput(stdout.trim());
		});
	});
}

async function waitForHttp(
	url: string,
	process: ManagedProcess,
	timeoutMs = 30_000
): Promise<void> {
	const deadline = Date.now() + timeoutMs;
	let lastError = '';

	while (Date.now() < deadline) {
		if (process.child.exitCode !== null || process.child.signalCode !== null) {
			throw new Error(
				`${process.logs()}\n${process.child.spawnargs.join(' ')} exited before ${url}`
			);
		}

		try {
			const response = await fetch(url);
			if (response.status < 500) {
				return;
			}
			lastError = `HTTP ${response.status}`;
		} catch (error) {
			lastError = error instanceof Error ? error.message : String(error);
		}

		await delay(250);
	}

	throw new Error(`Timed out waiting for ${url}: ${lastError}\n${process.logs()}`);
}

async function getFreePort(): Promise<number> {
	return new Promise((resolvePort, rejectPort) => {
		const server = net.createServer();
		server.unref();
		server.on('error', rejectPort);
		server.listen(0, '127.0.0.1', () => {
			const address = server.address();
			if (typeof address !== 'object' || address === null) {
				rejectPort(new Error('Unable to allocate a TCP port'));
				return;
			}

			const { port } = address;
			server.close(() => resolvePort(port));
		});
	});
}

function delay(ms: number): Promise<void> {
	return new Promise((resolveDelay) => setTimeout(resolveDelay, ms));
}
