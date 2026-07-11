import {
	expect,
	test as base,
	type APIResponse,
	type Page,
	type Response as PlaywrightResponse,
	type TestInfo
} from '@playwright/test';
import { execFile } from 'node:child_process';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, resolve } from 'node:path';
import { type Readable } from 'node:stream';
import { fileURLToPath } from 'node:url';
import net from 'node:net';
import { spawn, type ChildProcessByStdio, type SpawnOptionsWithoutStdio } from 'node:child_process';

const TEST_RECAPTCHA_TOKEN = 'hithero-test-recaptcha';
const PYTHON = process.env.PYTHON ?? 'python3';
const TEST_RUN_ID = `${Date.now().toString(36)}-${process.pid}`;
const __filename = fileURLToPath(import.meta.url);
const integrationDir = dirname(__filename);
const frontendDir = resolve(integrationDir, '../..');
const rootDir = resolve(frontendDir, '..');
const dbHelperPath = resolve(integrationDir, 'db_helper.py');

type TestStack = {
	backendOrigin: string;
	frontendOrigin: string;
	dbDir: string | null;
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

type PasswordResetTokenRecord = {
	email: string;
	token_present: boolean;
	used: number;
};

type RegisteredUserRecord = {
	email: string;
	create_count: number;
	password_is_hashed: boolean;
	password_matches: boolean;
};

type TeacherProfileRecord = {
	name: string;
	state: string;
	county: string;
	district: string;
	school: string;
	reg_user_id: number;
	wishlist_url: string;
	about_me: string;
	url_id_present: boolean;
};

type ForumPostRecord = {
	id: number;
	title: string;
	content: string;
	user_id: number;
	upvote_count: number;
	comment_count: number;
};

type SvelteKitRedirectAction = {
	type?: string;
	status?: number;
	location?: string;
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

function uniqueTestId(label: string, testInfo: TestInfo): string {
	const slug = label
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, '-')
		.replace(/^-|-$/g, '');

	return `${slug}-${TEST_RUN_ID}-w${testInfo.workerIndex}-r${testInfo.retry}`;
}

function uniqueEmail(label: string, testInfo: TestInfo): string {
	return `${uniqueTestId(label, testInfo)}@example.test`;
}

function uniqueSchool(label: string, testInfo: TestInfo) {
	const id = uniqueTestId(label, testInfo);

	return {
		state: `Integration State ${id}`,
		county: `Integration County ${id}`,
		district: `Integration District ${id}`,
		school: `Integration Elementary ${id}`
	};
}

const test = base.extend<Record<never, never>, { workerStack: TestStack }>({
	workerStack: [
		async ({ browserName }, use, workerInfo) => {
			void browserName;
			const workerStack = await startStack(workerInfo.workerIndex);
			stack = workerStack;

			try {
				await use(workerStack);
			} finally {
				await Promise.all([workerStack.frontend.stop(), workerStack.backend.stop()]);
				if (workerStack.dbDir) {
					await rm(workerStack.dbDir, { recursive: true, force: true });
				}
			}
		},
		{ scope: 'worker', auto: true }
	]
});

async function startStack(workerIndex: number): Promise<TestStack> {
	const backendPort = await getFreePort();
	const frontendPort = await getFreePort();
	const backendOrigin = `http://127.0.0.1:${backendPort}`;
	const frontendOrigin = `http://127.0.0.1:${frontendPort}`;
	const sharedDatabaseUrl = process.env.TEST_DATABASE_URL;
	const dbDir = sharedDatabaseUrl
		? null
		: await mkdtemp(resolve(tmpdir(), `hithero-integration-${workerIndex}-`));
	const testDatabaseUrl =
		sharedDatabaseUrl ?? `sqlite:///${resolve(dbDir as string, 'hithero.sqlite')}`;
	const env = {
		...process.env,
		APP_ENV: 'test',
		SECRET_KEY: 'integration-test-secret',
		TEST_DATABASE_URL: testDatabaseUrl,
		TEST_RECAPTCHA_TOKEN,
		CORS_ALLOW_ORIGINS: frontendOrigin
	};

	if (dbDir) {
		await runDbHelper(['reset'], env);
	}

	let backend: ManagedProcess | undefined;
	let frontend: ManagedProcess | undefined;

	try {
		backend = new ManagedProcess(
			`FastAPI worker ${workerIndex}`,
			PYTHON,
			['-m', 'uvicorn', 'app:app', '--host', '127.0.0.1', '--port', String(backendPort)],
			{ cwd: rootDir, env }
		);
		await waitForHttp(`${backendOrigin}/api/get_states/`, backend);

		frontend = new ManagedProcess(
			`SvelteKit worker ${workerIndex}`,
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
		if (dbDir) {
			await rm(dbDir, { recursive: true, force: true });
		}
		throw error;
	}
}

test('teacher login posts to FastAPI and redirects teachers without a profile', async ({
	page,
	context
}, testInfo) => {
	const email = uniqueEmail('teacher-login', testInfo);
	await seedLoginUser({
		email,
		password: 'correct horse battery staple',
		createCount: 0
	});

	await gotoFrontend(page, '/login');
	await page.getByLabel(/^Email/).fill(email);
	await page.getByLabel(/^Password/).fill('correct horse battery staple');

	const loginResponse = await submitAndWaitForBackendPost(
		page,
		() => page.getByRole('button', { name: 'Submit' }).click(),
		'/profile/login/'
	);

	expect(loginResponse.status()).toBe(200);
	await expect.poll(() => new URL(page.url()).pathname).toBe('/profile/create');
	expect(new URL(page.url()).origin).toBe(stack.frontendOrigin);

	const cookies = await context.cookies(stack.backendOrigin);
	const sessionCookie = cookies.find((cookie) => cookie.name === 'session');
	expect(sessionCookie?.value).toBeTruthy();
});

test('wrong password posts to FastAPI and stays on login with invalid credential message', async ({
	page
}, testInfo) => {
	const email = uniqueEmail('wrong-password', testInfo);
	await seedLoginUser({
		email,
		password: 'correct horse battery staple',
		createCount: 0
	});

	await gotoFrontend(page, '/login');
	await page.getByLabel(/^Email/).fill(email);
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

test('forgot password posts to FastAPI and creates a reset token for a registered user', async ({
	page
}, testInfo) => {
	const email = uniqueEmail('forgot-password', testInfo);
	await seedLoginUser({
		email,
		password: 'correct horse battery staple',
		createCount: 1
	});

	await gotoFrontend(page, '/forgot');
	await page.getByLabel(/^Email/).fill(email);

	const forgotResponse = await submitAndWaitForBackendPost(
		page,
		() => page.getByRole('button', { name: 'Submit' }).click(),
		'/profile/forgot_password/'
	);

	expect(forgotResponse.status()).toBe(200);
	await expect(page).toHaveURL(`${stack.frontendOrigin}/forgot`);
	await expect(page.getByRole('status')).toContainText(
		'If an account exists, a reset link will be sent to your email.'
	);

	const resetToken = await getPasswordResetToken(email);
	expect(resetToken).toMatchObject({
		email,
		token_present: true,
		used: 0
	});
});

test('reset password posts to FastAPI and updates the registered user password', async ({
	page
}, testInfo) => {
	const id = uniqueTestId('reset-password', testInfo);
	const email = `${id}@example.test`;
	const resetToken = `${id}-token`;
	const newPassword = 'new correct horse battery staple';
	await seedLoginUser({
		email,
		password: 'old correct horse battery staple',
		createCount: 1
	});
	await seedPasswordResetToken({ email, token: resetToken });

	await gotoFrontend(page, `/reset-password?token=${resetToken}`);
	await page.getByLabel(/^New Password/).fill(newPassword);
	await page.getByLabel(/^Confirm New Password/).fill(newPassword);

	const resetResponse = await submitAndWaitForBackendPost(
		page,
		() => page.getByRole('button', { name: 'Reset Password' }).click(),
		'/profile/reset_password/'
	);

	expect(resetResponse.status()).toBe(200);
	await expect(page).toHaveURL(`${stack.frontendOrigin}/reset-password?token=${resetToken}`);
	await expect(page.getByRole('status')).toContainText(
		'Password reset successfully. You can now log in.'
	);

	const usedToken = await getPasswordResetToken(email);
	expect(usedToken).toMatchObject({
		email,
		token_present: true,
		used: 1
	});

	const registeredUser = await getRegisteredUser(email, newPassword);
	expect(registeredUser).toMatchObject({
		email,
		create_count: 1,
		password_is_hashed: true,
		password_matches: true
	});
});

test('update password posts to FastAPI and changes the logged-in user password', async ({
	page
}, testInfo) => {
	const email = uniqueEmail('update-password', testInfo);
	const oldPassword = 'old correct horse battery staple';
	const newPassword = 'new correct horse battery staple';
	await seedLoginUser({
		email,
		password: oldPassword,
		createCount: 1
	});

	await gotoFrontend(page, '/login');
	await page.getByLabel(/^Email/).fill(email);
	await page.getByLabel(/^Password/).fill(oldPassword);

	const loginResponse = await submitAndWaitForBackendPost(
		page,
		() => page.getByRole('button', { name: 'Submit' }).click(),
		'/profile/login/'
	);
	expect(loginResponse.status()).toBe(200);

	await gotoFrontend(page, '/update-password');
	await page.getByLabel(/^Old Password/).fill(oldPassword);
	await page.getByLabel(/^New Password/).fill(newPassword);
	await page.getByLabel(/^Confirm New Password/).fill(newPassword);

	const updateResponse = await submitAndWaitForBackendPost(
		page,
		() => page.getByRole('button', { name: 'Submit' }).click(),
		'/profile/update_password/'
	);

	expect(updateResponse.status()).toBe(200);
	await expect.poll(() => new URL(page.url()).pathname).toBe('/teacher');

	const registeredUser = await getRegisteredUser(email, newPassword);
	expect(registeredUser).toMatchObject({
		email,
		create_count: 1,
		password_is_hashed: true,
		password_matches: true
	});
});

test('native update-password action redirects after changing the password', async ({
	page
}, testInfo) => {
	const email = uniqueEmail('native-update-password', testInfo);
	const oldPassword = 'old correct horse battery staple';
	const newPassword = 'new correct horse battery staple';
	await seedLoginUser({
		email,
		password: oldPassword,
		createCount: 1
	});

	await loginThroughSvelteAction(page, email, oldPassword);

	const updateResponse = await page.request.post(`${stack.frontendOrigin}/update-password`, {
		form: {
			old_password: oldPassword,
			new_password: newPassword,
			new_password_confirmed: newPassword
		},
		maxRedirects: 0
	});

	await expectSvelteKitActionRedirect(updateResponse, '/teacher');

	const registeredUser = await getRegisteredUser(email, newPassword);
	expect(registeredUser).toMatchObject({
		email,
		create_count: 1,
		password_is_hashed: true,
		password_matches: true
	});
});

test('profile creation posts to FastAPI and creates a TeacherList row', async ({
	page
}, testInfo) => {
	const school = uniqueSchool('profile-create', testInfo);
	const email = uniqueEmail('profile-create', testInfo);
	const teacherName = `Integration Profile Teacher ${uniqueTestId('profile-create', testInfo)}`;
	await seedSchool(school);
	const password = 'correct horse battery staple';
	await seedLoginUser({
		email,
		password,
		createCount: 0
	});

	await gotoFrontend(page, '/login');
	await page.getByLabel(/^Email/).fill(email);
	await page.getByLabel(/^Password/).fill(password);

	const loginResponse = await submitAndWaitForBackendPost(
		page,
		() => page.getByRole('button', { name: 'Submit' }).click(),
		'/profile/login/'
	);
	expect(loginResponse.status()).toBe(200);
	await expect(page).toHaveURL(`${stack.frontendOrigin}/profile/create`);
	await expect(page.getByLabel(/^State/)).toContainText(school.state);

	await page.getByLabel(/^Full Name/).fill(teacherName);
	await page.getByLabel(/^State/).selectOption(school.state);
	await expect(page.getByLabel(/^County/)).toContainText(school.county);
	await page.getByLabel(/^County/).selectOption(school.county);
	await expect(page.getByLabel(/^School District/)).toContainText(school.district);
	await page.getByLabel(/^School District/).selectOption(school.district);
	await expect(page.getByLabel(/^School required$/)).toContainText(school.school);
	await page.getByLabel(/^School required$/).selectOption(school.school);
	await page.getByLabel(/^About Me/).fill('I help students build durable skills.');
	await page.getByLabel(/^Amazon Wishlist URL/).fill('https://example.com/wishlist');

	const createResponse = await submitAndWaitForBackendPost(
		page,
		() => page.getByRole('button', { name: 'Submit' }).click(),
		'/profile/create_teacher_profile/'
	);

	expect(createResponse.status()).toBe(200);
	await expect(page.getByRole('status')).toContainText('Teacher created successfully');

	const teacherProfile = await getTeacherProfile(email);
	expect(teacherProfile).toMatchObject({
		name: teacherName,
		state: school.state,
		county: school.county,
		district: school.district,
		school: school.school,
		wishlist_url: 'https://example.com/wishlist&tag=h0mer00mher0-20',
		about_me: 'I help students build durable skills.',
		url_id_present: true
	});

	const registeredUser = await getRegisteredUser(email, password);
	expect(registeredUser.create_count).toBe(1);
});

test('teacher page loads real FastAPI data through SvelteKit for logged-in teachers', async ({
	page
}, testInfo) => {
	const id = uniqueTestId('teacher-page', testInfo);
	const email = `${id}@example.test`;
	const school = uniqueSchool('teacher-page', testInfo);
	const teacherName = `Integration Page Teacher ${id}`;
	const urlId = `integration-page-teacher-${id}`;
	const password = 'correct horse battery staple';
	await seedLoginUser({
		email,
		password,
		createCount: 1
	});
	await seedTeacherProfile({
		email,
		name: teacherName,
		state: school.state,
		county: school.county,
		district: school.district,
		school: school.school,
		wishlistUrl: 'https://example.com/integration-wishlist',
		aboutMe: 'Integration students need fresh classroom supplies.',
		urlId
	});

	await gotoFrontend(page, '/login');
	await page.getByLabel(/^Email/).fill(email);
	await page.getByLabel(/^Password/).fill(password);

	const loginResponse = await submitAndWaitForBackendPost(
		page,
		() => page.getByRole('button', { name: 'Submit' }).click(),
		'/profile/login/'
	);
	expect(loginResponse.status()).toBe(200);

	await gotoFrontend(page, '/teacher');

	await expect(page.getByRole('heading', { level: 1, name: teacherName })).toBeVisible();
	await expect(page.getByText(`School: ${school.school}`)).toBeVisible();
	await expect(page.getByText(`Location: ${school.county}, ${school.state}`)).toBeVisible();
	await expect(page.getByText('Integration students need fresh classroom supplies.')).toBeVisible();
	await expect(page.getByRole('link', { name: 'View Wishlist' })).toHaveAttribute(
		'href',
		'https://example.com/integration-wishlist'
	);
	await expect(page.getByRole('link', { name: 'Edit Info' })).toBeVisible();
	await expect(page.getByRole('link', { name: 'Update Password' })).toBeVisible();
});

test('public teacher URL renders server HTML and metadata from FastAPI data', async ({
	page
}, testInfo) => {
	const id = uniqueTestId('public-teacher', testInfo);
	const email = `${id}@example.test`;
	const school = uniqueSchool('public-teacher', testInfo);
	const teacherName = `Public Integration Teacher ${id}`;
	const urlId = `public-integration-teacher-${id}`;
	await seedLoginUser({
		email,
		password: 'correct horse battery staple',
		createCount: 1
	});
	await seedTeacherProfile({
		email,
		name: teacherName,
		state: school.state,
		county: school.county,
		district: school.district,
		school: school.school,
		wishlistUrl: 'https://example.com/public-wishlist',
		aboutMe: 'This public teacher page was rendered on the server.',
		urlId
	});

	const response = await page.goto(`${stack.frontendOrigin}/teacher/${urlId}`, {
		waitUntil: 'domcontentloaded'
	});
	expect(response?.status()).toBe(200);
	await expect(page).toHaveTitle(`${teacherName} - Homeroom Heroes Teacher Profile`);
	await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
		'href',
		`https://www.helpteachers.net/teacher/${urlId}`
	);

	const initialHtml = await response?.text();
	expect(initialHtml).toContain(teacherName);
	expect(initialHtml).toContain('This public teacher page was rendered on the server.');

	await expect(page.getByRole('heading', { level: 1, name: teacherName })).toBeVisible();
	await expect(page.getByText(`School: ${school.school}`)).toBeVisible();
	await expect(page.getByText(`Location: ${school.county}, ${school.state}`)).toBeVisible();
	await expect(page.getByRole('link', { name: 'View Wishlist' })).toHaveAttribute(
		'href',
		'https://example.com/public-wishlist'
	);
	await expect(page.getByRole('link', { name: 'Edit Info' })).toHaveCount(0);
});

test('public teacher URL returns a real 404 for missing teachers', async ({ page }) => {
	const response = await page.goto(`${stack.frontendOrigin}/teacher/missing-teacher`, {
		waitUntil: 'domcontentloaded'
	});

	expect(response?.status()).toBe(404);
	await expect(page.getByText('Teacher not found')).toBeVisible();
});

test('profile edit posts an about-me update to FastAPI and persists it', async ({
	page
}, testInfo) => {
	const id = uniqueTestId('profile-edit', testInfo);
	const email = `${id}@example.test`;
	const school = uniqueSchool('profile-edit', testInfo);
	const teacherName = `Editable Integration Teacher ${id}`;
	const urlId = `editable-integration-teacher-${id}`;
	await seedSchool(school);
	const password = 'correct horse battery staple';
	await seedLoginUser({
		email,
		password,
		createCount: 1
	});
	await seedTeacherProfile({
		email,
		name: teacherName,
		state: school.state,
		county: school.county,
		district: school.district,
		school: school.school,
		wishlistUrl: 'https://example.com/edit-wishlist',
		aboutMe: 'Original classroom story.',
		urlId
	});

	await gotoFrontend(page, '/login');
	await page.getByLabel(/^Email/).fill(email);
	await page.getByLabel(/^Password/).fill(password);

	const loginResponse = await submitAndWaitForBackendPost(
		page,
		() => page.getByRole('button', { name: 'Submit' }).click(),
		'/profile/login/'
	);
	expect(loginResponse.status()).toBe(200);

	await gotoFrontend(page, '/profile/edit');
	await expect(page.getByLabel(/^Name/)).toHaveValue(teacherName);
	await expect(page.getByLabel(/^About Me/)).toHaveValue('Original classroom story.');

	await page.getByLabel(/^About Me/).fill('Updated classroom story from SvelteKit.');
	const updateResponse = await submitAndWaitForBackendPost(
		page,
		() => page.getByRole('button', { name: 'Update About Me' }).click(),
		'/profile/update_info/'
	);

	expect(updateResponse.status()).toBe(200);
	await expect.poll(() => new URL(page.url()).pathname).toBe('/teacher');

	const teacherProfile = await getTeacherProfile(email);
	expect(teacherProfile.about_me).toBe('Updated classroom story from SvelteKit.');
});

test('native profile edit action redirects after persisting an about-me update', async ({
	page
}, testInfo) => {
	const id = uniqueTestId('native-profile-edit', testInfo);
	const email = `${id}@example.test`;
	const school = uniqueSchool('native-profile-edit', testInfo);
	const teacherName = `Native Editable Teacher ${id}`;
	const urlId = `native-editable-teacher-${id}`;
	const password = 'correct horse battery staple';
	await seedSchool(school);
	await seedLoginUser({
		email,
		password,
		createCount: 1
	});
	await seedTeacherProfile({
		email,
		name: teacherName,
		state: school.state,
		county: school.county,
		district: school.district,
		school: school.school,
		wishlistUrl: 'https://example.com/native-edit-wishlist',
		aboutMe: 'Original native classroom story.',
		urlId
	});
	await loginThroughSvelteAction(page, email, password);

	const updateResponse = await page.request.post(
		`${stack.frontendOrigin}/profile/edit?/updateInfo`,
		{
			form: {
				aboutMe: 'Updated native classroom story from SvelteKit.'
			},
			maxRedirects: 0
		}
	);

	await expectSvelteKitActionRedirect(updateResponse, '/teacher?profile_update=Info%20updated.');

	const teacherProfile = await getTeacherProfile(email);
	expect(teacherProfile.about_me).toBe('Updated native classroom story from SvelteKit.');
});

test('forum list loads real FastAPI posts through SvelteKit', async ({ page }, testInfo) => {
	const id = uniqueTestId('forum-list', testInfo);
	const email = `${id}@example.test`;
	const password = 'correct horse battery staple';
	const title = `Integration forum discussion ${id}`;
	await seedLoginUser({
		email,
		password,
		createCount: 1
	});
	await seedForumPost({
		email,
		title,
		content: 'This forum post came from the isolated FastAPI database.',
		createdAt: '2026-06-10T12:00:00',
		upvoteCount: 5,
		commentCount: 2
	});
	await loginThroughSvelteAction(page, email, password);

	await gotoFrontend(page, '/forum');

	await expect(page.getByRole('heading', { level: 1, name: "The Teachers' Lounge" })).toBeVisible();
	const discussionPost = page.getByRole('link').filter({ hasText: title });
	await expect(discussionPost).toBeVisible();
	await expect(discussionPost.getByText('isolated FastAPI database')).toBeVisible();
	await expect(discussionPost.getByText('5 upvotes')).toBeVisible();
	await expect(discussionPost.getByText('2 comments')).toBeVisible();
});

test('forum post detail loads real FastAPI post and comments through SvelteKit', async ({
	page
}, testInfo) => {
	const id = uniqueTestId('forum-detail', testInfo);
	const email = `${id}@example.test`;
	const password = 'correct horse battery staple';
	const title = `Integration forum detail discussion ${id}`;
	await seedLoginUser({
		email,
		password,
		createCount: 1
	});
	await seedForumPost({
		email,
		title,
		content: 'This detailed forum post came from the isolated FastAPI database.',
		createdAt: '2026-06-10T12:00:00',
		upvoteCount: 7,
		commentCount: 1
	});
	await seedForumComment({
		email,
		postTitle: title,
		content: 'This detail comment came from the isolated FastAPI database.',
		createdAt: '2026-06-11T12:00:00'
	});
	const post = await getForumPost(title);
	await loginThroughSvelteAction(page, email, password);

	await gotoFrontend(page, `/forum/post?id=${post.id}`);

	await expect(page.getByRole('heading', { level: 1, name: 'Discussion Detail' })).toBeVisible();
	await expect(page.getByRole('heading', { level: 2, name: title })).toBeVisible();
	await expect(
		page.getByText('detailed forum post came from the isolated FastAPI database')
	).toBeVisible();
	await expect(page.getByText('7 upvotes')).toBeVisible();
	await expect(page.getByText('1 comments', { exact: true })).toBeVisible();
	await expect(
		page.getByText('detail comment came from the isolated FastAPI database')
	).toBeVisible();
});

test('logged-in forum users can vote and comment through SvelteKit', async ({ page }, testInfo) => {
	const id = uniqueTestId('forum-actions', testInfo);
	const email = `${id}@example.test`;
	const password = 'correct horse battery staple';
	const title = `Interactive integration discussion ${id}`;
	await seedLoginUser({ email, password, createCount: 1 });
	await seedForumPost({
		email,
		title,
		content: 'This discussion exercises real forum mutations.',
		createdAt: '2026-06-10T12:00:00',
		upvoteCount: 0,
		commentCount: 0
	});
	const seededPost = await getForumPost(title);

	await gotoFrontend(page, '/login');
	await page.getByLabel(/^Email/).fill(email);
	await page.getByLabel(/^Password/).fill(password);
	await submitAndWaitForBackendPost(
		page,
		() => page.getByRole('button', { name: 'Submit' }).click(),
		'/profile/login/'
	);

	await gotoFrontend(page, `/forum/post?id=${seededPost.id}`);
	const voteResponsePromise = page.waitForResponse(
		(response) =>
			response.request().method() === 'POST' &&
			new URL(response.url()).pathname === `/forum/posts/${seededPost.id}/vote`
	);
	await page.getByRole('button', { name: 'Upvote' }).click();
	expect((await voteResponsePromise).status()).toBe(200);
	await expect(page.getByText('1 upvotes')).toBeVisible();

	await page.getByLabel('Add a comment').fill('A real integration comment.');
	const commentResponse = await submitAndWaitForBackendPost(
		page,
		() => page.getByRole('button', { name: 'Post Comment' }).click(),
		`/forum/posts/${seededPost.id}/comment`
	);
	expect(commentResponse.status()).toBe(200);
	await expect(page.getByText('A real integration comment.')).toBeVisible();

	const persistedPost = await getForumPost(title);
	expect(persistedPost.upvote_count).toBe(1);
	expect(persistedPost.comment_count).toBe(1);
});

test('registration posts to FastAPI and queues a NewUsers validation row', async ({
	page
}, testInfo) => {
	const id = uniqueTestId('registration', testInfo);
	const school = uniqueSchool('registration', testInfo);
	const email = `${id}@example.test`;
	const teacherName = `Integration Teacher ${id}`;
	await seedSchool(school);
	await installRecaptchaStub(page);

	const password = 'registration password';

	await gotoFrontend(page, '/register');
	await expect(page.getByLabel(/^State/)).toContainText(school.state);

	await page.getByLabel(/^Name/).fill(teacherName);
	await page.getByLabel(/^Email/).fill(email);
	await page.getByLabel(/^Phone Number/).fill('555-0199');
	await page.getByLabel(/^Password/).fill(password);
	await page.getByLabel(/^Confirm Password/).fill(password);
	await page.getByLabel(/^State/).selectOption(school.state);
	await expect(page.getByLabel(/^County/)).toContainText(school.county);
	await page.getByLabel(/^County/).selectOption(school.county);
	await expect(page.getByLabel(/^School District/)).toContainText(school.district);
	await page.getByLabel(/^School District/).selectOption(school.district);
	await expect(page.getByLabel(/^School required$/)).toContainText(school.school);
	await page.getByLabel(/^School required$/).selectOption(school.school);
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
		name: teacherName,
		phone_number: '555-0199',
		state: school.state,
		county: school.county,
		district: school.district,
		school: school.school,
		role: 'teacher',
		report: 0,
		emailed: 0,
		password_is_hashed: true
	});
});

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

async function seedPasswordResetToken(args: { email: string; token: string }): Promise<void> {
	await runDbHelper(
		['seed-password-reset-token', '--email', args.email, '--token', args.token],
		stack.env
	);
}

async function seedTeacherProfile(args: {
	email: string;
	name: string;
	state: string;
	county: string;
	district: string;
	school: string;
	wishlistUrl: string;
	aboutMe: string;
	urlId: string;
}): Promise<void> {
	await runDbHelper(
		[
			'seed-teacher-profile',
			'--email',
			args.email,
			'--name',
			args.name,
			'--state',
			args.state,
			'--county',
			args.county,
			'--district',
			args.district,
			'--school',
			args.school,
			'--wishlist-url',
			args.wishlistUrl,
			'--about-me',
			args.aboutMe,
			'--url-id',
			args.urlId
		],
		stack.env
	);
}

async function seedForumPost(args: {
	email: string;
	title: string;
	content: string;
	createdAt: string;
	upvoteCount: number;
	commentCount: number;
}): Promise<void> {
	await runDbHelper(
		[
			'seed-forum-post',
			'--email',
			args.email,
			'--title',
			args.title,
			'--content',
			args.content,
			'--created-at',
			args.createdAt,
			'--upvote-count',
			String(args.upvoteCount),
			'--comment-count',
			String(args.commentCount)
		],
		stack.env
	);
}

async function seedForumComment(args: {
	email: string;
	postTitle: string;
	content: string;
	createdAt: string;
}): Promise<void> {
	await runDbHelper(
		[
			'seed-forum-comment',
			'--email',
			args.email,
			'--post-title',
			args.postTitle,
			'--content',
			args.content,
			'--created-at',
			args.createdAt
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

async function getRegisteredUser(
	email: string,
	plainPassword: string
): Promise<RegisteredUserRecord> {
	const output = await runDbHelper(
		['get-registered-user', '--email', email, '--plain-password', plainPassword],
		stack.env
	);
	const record = JSON.parse(output) as RegisteredUserRecord | null;

	expect(record).not.toBeNull();
	return record as RegisteredUserRecord;
}

async function getTeacherProfile(email: string): Promise<TeacherProfileRecord> {
	const output = await runDbHelper(['get-teacher-profile', '--email', email], stack.env);
	const record = JSON.parse(output) as TeacherProfileRecord | null;

	expect(record).not.toBeNull();
	return record as TeacherProfileRecord;
}

async function getPasswordResetToken(email: string): Promise<PasswordResetTokenRecord> {
	const output = await runDbHelper(['get-password-reset-token', '--email', email], stack.env);
	const record = JSON.parse(output) as PasswordResetTokenRecord | null;

	expect(record).not.toBeNull();
	return record as PasswordResetTokenRecord;
}

async function getForumPost(title: string): Promise<ForumPostRecord> {
	const output = await runDbHelper(['get-forum-post', '--title', title], stack.env);
	const record = JSON.parse(output) as ForumPostRecord | null;

	expect(record).not.toBeNull();
	return record as ForumPostRecord;
}

async function loginThroughSvelteAction(
	page: Page,
	email: string,
	password: string
): Promise<void> {
	const response = await page.request.post(`${stack.frontendOrigin}/login`, {
		form: { email, password },
		maxRedirects: 0
	});

	await expectSvelteKitActionRedirect(response, '/');
	await copySessionCookieToPage(page, response);
}

async function expectSvelteKitActionRedirect(
	response: APIResponse,
	location: string
): Promise<void> {
	if (response.status() === 303) {
		expect(response.headers().location).toBe(location);
		return;
	}

	expect(response.status()).toBe(200);
	const body = (await response.json().catch(() => null)) as SvelteKitRedirectAction | null;
	expect(body).toMatchObject({
		type: 'redirect',
		status: 303,
		location
	});
}

async function copySessionCookieToPage(page: Page, response: APIResponse): Promise<void> {
	const setCookie = response.headers()['set-cookie'];
	const match = setCookie?.match(/^session=([^;]+)/);
	if (!match) {
		return;
	}

	await page.context().addCookies([
		{
			name: 'session',
			value: decodeURIComponent(match[1]),
			url: stack.frontendOrigin,
			httpOnly: true,
			sameSite: 'Lax'
		}
	]);
}

async function submitAndWaitForBackendPost(
	page: Page,
	action: () => Promise<void>,
	path: string
): Promise<PlaywrightResponse> {
	const responsePromise = page.waitForResponse(
		(response) =>
			response.url() === `${stack.backendOrigin}${path}` && response.request().method() === 'POST'
	);
	await action();
	return responsePromise;
}

async function gotoFrontend(page: Page, path: string): Promise<void> {
	await page.goto(`${stack.frontendOrigin}${path}`, { waitUntil: 'load' });
	await page.waitForLoadState('networkidle');
}

async function installRecaptchaStub(page: Page): Promise<void> {
	await page.route('https://www.google.com/recaptcha/**', async (route) => {
		await route.fulfill({
			contentType: 'application/javascript',
			body: `window.grecaptcha = {
				render: () => 1,
				getResponse: () => '${TEST_RECAPTCHA_TOKEN}',
				reset: () => {}
			};`
		});
	});
	await page.addInitScript((token: string) => {
		(
			window as Window & {
				grecaptcha?: {
					render: () => number;
					getResponse: () => string;
					reset: () => void;
				};
			}
		).grecaptcha = {
			render: () => 1,
			getResponse: () => token,
			reset: () => {}
		};
	}, TEST_RECAPTCHA_TOKEN);
}

async function runDbHelper(args: string[], env: NodeJS.ProcessEnv): Promise<string> {
	return new Promise((resolveOutput, rejectOutput) => {
		execFile(PYTHON, [dbHelperPath, ...args], { cwd: rootDir, env }, (error, stdout, stderr) => {
			if (error) {
				rejectOutput(
					new Error(`DB helper failed: ${PYTHON} ${dbHelperPath} ${args.join(' ')}\n${stderr}`)
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
