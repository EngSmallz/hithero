import { expect, test } from '@playwright/test';
import { installAuthenticatedSession } from '$lib/test/session';

test.describe('form fallbacks without JavaScript', () => {
	test.use({ javaScriptEnabled: false });

	test('keeps contact submission on the Svelte page when reCAPTCHA cannot run', async ({
		page
	}) => {
		await page.goto('/contact', { waitUntil: 'domcontentloaded' });
		await page.getByLabel(/^Name/).fill('Fallback User');
		await page.getByLabel(/^Email/).fill('fallback@example.test');
		await page.getByLabel(/^Subject/).fill('Fallback check');
		await page.getByLabel(/^Message/).fill('This should not expose backend JSON.');
		await page.getByRole('button', { name: 'Submit' }).click({ force: true });

		await expect(page).toHaveURL('/contact');
		await expect(page.getByRole('alert')).toContainText('enable JavaScript');
	});

	test('keeps registration native action on the Svelte page', async ({ page }) => {
		await page.goto('/register', { waitUntil: 'domcontentloaded' });

		await expect(page.locator('form')).toHaveAttribute('action', /\/register$/);
	});

	test('keeps invalid login on the Svelte page', async ({ page }) => {
		await page.goto('/login?redirect=%2Fvalidation', { waitUntil: 'domcontentloaded' });
		await page.getByLabel(/^Email/).fill('missing-user@example.test');
		await page.getByLabel(/^Password/).fill('wrong-password');
		await page.getByRole('button', { name: 'Submit' }).click();

		await expect(page).toHaveURL('/login?redirect=%2Fvalidation');
		await expect(page.getByRole('alert')).toContainText('Invalid login credentials.');
	});

	test('keeps forgot-password submission on the Svelte page', async ({ page }, testInfo) => {
		const id = `${testInfo.workerIndex}-${Date.now()}`;

		await page.goto('/forgot', { waitUntil: 'domcontentloaded' });
		await page.getByLabel(/^Email/).fill(`unknown-${id}@example.test`);
		await page.getByRole('button', { name: 'Submit' }).click();

		await expect(page).toHaveURL('/forgot');
		await expect(page.getByRole('status')).toContainText(
			'If an account exists, a reset link will be sent to your email.'
		);
	});

	test('keeps reset-password validation on the Svelte page', async ({ page }) => {
		await page.goto('/reset-password?token=fallback-token', { waitUntil: 'domcontentloaded' });
		await page.getByLabel(/^New Password/).fill('one-password');
		await page.getByLabel(/^Confirm New Password/).fill('another-password');
		await page.getByRole('button', { name: 'Reset Password' }).click();

		await expect(page).toHaveURL('/reset-password?token=fallback-token');
		await expect(page.getByRole('alert')).toContainText('Passwords do not match.');
	});

	test('keeps update-password submission on the Svelte page', async ({ page, context }) => {
		await installAuthenticatedSession(context);

		await page.goto('/update-password', { waitUntil: 'domcontentloaded' });
		await page.getByLabel(/^Old Password/).fill('old-password');
		await page.getByLabel(/^New Password/).fill('new-password');
		await page.getByLabel(/^Confirm New Password/).fill('different-password');
		await page.getByRole('button', { name: 'Submit' }).click();

		await expect(page).toHaveURL('/update-password');
		await expect(page.locator('body')).not.toContainText('{');
		await expect(page.getByRole('alert')).toBeVisible();
	});

	test('submits profile creation through the SvelteKit action with manual school fields', async ({
		page,
		context
	}) => {
		await installAuthenticatedSession(context);

		await page.goto('/profile/create', { waitUntil: 'domcontentloaded' });

		await expect(page.locator('form')).toHaveAttribute('action', /\/profile\/create$/);
		await expect(
			page.getByRole('heading', { level: 1, name: 'Create Teacher Profile' })
		).toBeVisible();
		await page.getByLabel(/^Full Name/).fill('No JavaScript Teacher');
		await page.getByLabel('State (manual entry)').fill('Washington');
		await page.getByLabel('County (manual entry)').fill('King');
		await page.getByLabel('School District (manual entry)').fill('Seattle Public Schools');
		await page.getByLabel('School (manual entry)').fill('Evergreen Elementary');
		await page.getByLabel(/^About Me/).fill('This submission stays on the clean Svelte route.');
		await page.getByLabel(/^Amazon Wishlist URL/).fill('https://example.com/no-js-wishlist');
		await page.getByRole('button', { name: 'Submit' }).click({ force: true });

		await expect(page).toHaveURL('/profile/create');
		await expect(page.getByRole('alert')).toContainText('Profile already created');
		await expect(page.locator('body')).not.toContainText('{"message"');
	});

	test('renders and submits the profile editor without JavaScript', async ({ page, context }) => {
		await installAuthenticatedSession(context);

		const response = await page.goto('/profile/edit', { waitUntil: 'domcontentloaded' });
		expect(await response?.text()).toContain('Avery Adams');
		await expect(page.getByLabel(/^Name/)).toHaveValue('Avery Adams');
		await expect(page.getByLabel('State (manual entry)')).toHaveValue('Washington');
		await page.getByRole('button', { name: 'Update School' }).click();

		await expect(page).toHaveURL(/\/teacher\?profile_update=/);
		await expect(page.locator('body')).not.toContainText('{"message"');
	});

	test('identifies forum post interactions as JavaScript-required', async ({ page, context }) => {
		await installAuthenticatedSession(context);

		await page.goto('/forum/post?id=123', { waitUntil: 'domcontentloaded' });

		await expect(
			page.getByRole('alert').filter({
				hasText: 'Voting, commenting, and editing discussions require JavaScript'
			})
		).toBeVisible();
		await expect(page.locator('body')).not.toContainText('/forum/posts/123/comment');
	});

	test('identifies admin actions as JavaScript-required', async ({ page, context }) => {
		await installAuthenticatedSession(context, 'admin');

		await page.goto('/admin', { waitUntil: 'domcontentloaded' });

		await expect(page.getByRole('alert')).toContainText(
			'Admin report and account deletion tools require JavaScript'
		);
		await expect(page.locator('form')).toHaveCount(2);
	});

	test('identifies validation actions as JavaScript-required', async ({ page, context }) => {
		await installAuthenticatedSession(context);

		await page.goto('/validation', { waitUntil: 'domcontentloaded' });

		await expect(page.getByRole('alert')).toContainText(
			'Validation, report, email, and delete actions require JavaScript'
		);
	});

	test('identifies teacher image and share actions as JavaScript-required', async ({
		page,
		context
	}) => {
		await installAuthenticatedSession(context);

		await page.goto('/teacher', { waitUntil: 'domcontentloaded' });

		await expect(page.getByRole('alert')).toContainText(
			'Image updates and Share Page require JavaScript'
		);
	});
});
