import {
	expect,
	test as base,
	type Page,
	type Response as PlaywrightResponse
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
			'python',
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
}) => {
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
	expect(new URL(page.url()).origin).toBe(stack.frontendOrigin);

	const cookies = await context.cookies(stack.backendOrigin);
	const sessionCookie = cookies.find((cookie) => cookie.name === 'session');
	expect(sessionCookie?.value).toBeTruthy();
});

test('wrong password posts to FastAPI and stays on login with invalid credential message', async ({
	page
}) => {
	const email = 'wrong.password.integration@example.test';
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
}) => {
	const email = 'forgot.integration@example.test';
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
}) => {
	const email = 'reset.integration@example.test';
	const resetToken = 'integration-reset-token';
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
}) => {
	const email = 'update.password.integration@example.test';
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

test('profile creation posts to FastAPI and creates a TeacherList row', async ({ page }) => {
	await seedSchool({
		state: 'Integration State',
		county: 'Integration County',
		district: 'Integration District',
		school: 'Integration Elementary'
	});
	const email = 'profile.integration@example.test';
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
	await expect(page.getByLabel(/^State/)).toContainText('Integration State');

	await page.getByLabel(/^Full Name/).fill('Integration Profile Teacher');
	await page.getByLabel(/^State/).selectOption('Integration State');
	await expect(page.getByLabel(/^County/)).toContainText('Integration County');
	await page.getByLabel(/^County/).selectOption('Integration County');
	await expect(page.getByLabel(/^School District/)).toContainText('Integration District');
	await page.getByLabel(/^School District/).selectOption('Integration District');
	await expect(page.getByLabel(/^School required$/)).toContainText('Integration Elementary');
	await page.getByLabel(/^School required$/).selectOption('Integration Elementary');
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
		name: 'Integration Profile Teacher',
		state: 'Integration State',
		county: 'Integration County',
		district: 'Integration District',
		school: 'Integration Elementary',
		wishlist_url: 'https://example.com/wishlist&tag=h0mer00mher0-20',
		about_me: 'I help students build durable skills.',
		url_id_present: true
	});

	const registeredUser = await getRegisteredUser(email, password);
	expect(registeredUser.create_count).toBe(1);
});

test('teacher page loads real FastAPI data through SvelteKit for logged-in teachers', async ({
	page
}) => {
	const email = 'teacher.page.integration@example.test';
	const password = 'correct horse battery staple';
	await seedLoginUser({
		email,
		password,
		createCount: 1
	});
	await seedTeacherProfile({
		email,
		name: 'Integration Page Teacher',
		state: 'Integration State',
		county: 'Integration County',
		district: 'Integration District',
		school: 'Integration Elementary',
		wishlistUrl: 'https://example.com/integration-wishlist',
		aboutMe: 'Integration students need fresh classroom supplies.',
		urlId: 'integration-page-teacher'
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

	await expect(
		page.getByRole('heading', { level: 1, name: 'Integration Page Teacher' })
	).toBeVisible();
	await expect(page.getByText('School: Integration Elementary')).toBeVisible();
	await expect(page.getByText('Location: Integration County, Integration State')).toBeVisible();
	await expect(page.getByText('Integration students need fresh classroom supplies.')).toBeVisible();
	await expect(page.getByRole('link', { name: 'View Wishlist' })).toHaveAttribute(
		'href',
		'https://example.com/integration-wishlist'
	);
	await expect(page.getByRole('link', { name: 'Edit Info' })).toBeVisible();
	await expect(page.getByRole('link', { name: 'Update Password' })).toBeVisible();
});

test('public teacher URL renders server HTML and metadata from FastAPI data', async ({ page }) => {
	const email = 'public.teacher.integration@example.test';
	await seedLoginUser({
		email,
		password: 'correct horse battery staple',
		createCount: 1
	});
	await seedTeacherProfile({
		email,
		name: 'Public Integration Teacher',
		state: 'Integration State',
		county: 'Integration County',
		district: 'Integration District',
		school: 'Integration Elementary',
		wishlistUrl: 'https://example.com/public-wishlist',
		aboutMe: 'This public teacher page was rendered on the server.',
		urlId: 'public-integration-teacher'
	});

	const response = await page.goto(`${stack.frontendOrigin}/teacher/public-integration-teacher`, {
		waitUntil: 'domcontentloaded'
	});
	expect(response?.status()).toBe(200);
	await expect(page).toHaveTitle('Public Integration Teacher - Homeroom Heroes Teacher Profile');
	await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
		'href',
		'https://www.helpteachers.net/teacher/public-integration-teacher'
	);

	const initialHtml = await response?.text();
	expect(initialHtml).toContain('Public Integration Teacher');
	expect(initialHtml).toContain('This public teacher page was rendered on the server.');

	await expect(
		page.getByRole('heading', { level: 1, name: 'Public Integration Teacher' })
	).toBeVisible();
	await expect(page.getByText('School: Integration Elementary')).toBeVisible();
	await expect(page.getByText('Location: Integration County, Integration State')).toBeVisible();
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

test('profile edit posts an about-me update to FastAPI and persists it', async ({ page }) => {
	await seedSchool({
		state: 'Integration State',
		county: 'Integration County',
		district: 'Integration District',
		school: 'Integration Elementary'
	});
	const email = 'profile.edit.integration@example.test';
	const password = 'correct horse battery staple';
	await seedLoginUser({
		email,
		password,
		createCount: 1
	});
	await seedTeacherProfile({
		email,
		name: 'Editable Integration Teacher',
		state: 'Integration State',
		county: 'Integration County',
		district: 'Integration District',
		school: 'Integration Elementary',
		wishlistUrl: 'https://example.com/edit-wishlist',
		aboutMe: 'Original classroom story.',
		urlId: 'editable-integration-teacher'
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
	await expect(page.getByLabel(/^Name/)).toHaveValue('Editable Integration Teacher');
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

test('forum list loads real FastAPI posts through SvelteKit', async ({ page }) => {
	const email = 'forum.integration@example.test';
	await seedLoginUser({
		email,
		password: 'correct horse battery staple',
		createCount: 1
	});
	await seedForumPost({
		email,
		title: 'Integration forum discussion',
		content: 'This forum post came from the isolated FastAPI database.',
		createdAt: '2026-06-10T12:00:00',
		upvoteCount: 5,
		commentCount: 2
	});

	await gotoFrontend(page, '/forum');

	await expect(page.getByRole('heading', { level: 1, name: "The Teachers' Lounge" })).toBeVisible();
	const discussionPost = page.getByRole('link', { name: /Integration forum discussion/ });
	await expect(discussionPost).toBeVisible();
	await expect(discussionPost.getByText('isolated FastAPI database')).toBeVisible();
	await expect(discussionPost.getByText('5 upvotes')).toBeVisible();
	await expect(discussionPost.getByText('2 comments')).toBeVisible();
});

test('forum post detail loads real FastAPI post and comments through SvelteKit', async ({
	page
}) => {
	const email = 'forum.detail.integration@example.test';
	const title = 'Integration forum detail discussion';
	await seedLoginUser({
		email,
		password: 'correct horse battery staple',
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

	await gotoFrontend(page, `/forum/post?id=${post.id}`);

	await expect(page.getByRole('heading', { level: 1, name: 'Discussion Detail' })).toBeVisible();
	await expect(
		page.getByRole('heading', { level: 2, name: 'Integration forum detail discussion' })
	).toBeVisible();
	await expect(
		page.getByText('detailed forum post came from the isolated FastAPI database')
	).toBeVisible();
	await expect(page.getByText('7 upvotes')).toBeVisible();
	await expect(page.getByText('1 comments', { exact: true })).toBeVisible();
	await expect(
		page.getByText('detail comment came from the isolated FastAPI database')
	).toBeVisible();
});

test('logged-in forum users can vote and comment through SvelteKit', async ({ page }) => {
	const email = 'forum.actions.integration@example.test';
	const password = 'correct horse battery staple';
	const title = 'Interactive integration discussion';
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

test('registration posts to FastAPI and queues a NewUsers validation row', async ({ page }) => {
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
