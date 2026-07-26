import { expect, test } from '@playwright/test';
import { installAuthenticatedSession } from '$lib/test/session';

test.describe('/validation', () => {
	test('redirects unauthenticated visitors to login before rendering', async ({ page }) => {
		await page.goto('/validation', { waitUntil: 'domcontentloaded' });

		await expect(page).toHaveURL('/login?redirect=%2Fvalidation');
	});

	test('returns 403 for authenticated users without teacher/admin role', async ({
		page,
		context
	}) => {
		await installAuthenticatedSession(context, 'user');

		const response = await page.goto('/validation', { waitUntil: 'domcontentloaded' });

		expect(response?.status()).toBe(403);
		await expect(page.getByRole('heading', { level: 1, name: 'Forbidden' })).toBeVisible();
	});

	test('renders validation tools for teachers', async ({ page, context }) => {
		await installAuthenticatedSession(context, 'teacher');

		await page.goto('/validation', { waitUntil: 'domcontentloaded' });

		await expect(
			page.getByRole('heading', { level: 1, name: 'How Validation Works' })
		).toBeVisible();
		await expect(page.getByRole('region', { name: 'Validation List' })).toBeVisible();
		await expect(page.locator('meta[name="robots"]')).toHaveAttribute(
			'content',
			'noindex, nofollow'
		);
	});

	test('renders validation tools for admins', async ({ page, context }) => {
		await installAuthenticatedSession(context, 'admin');

		await page.goto('/validation', { waitUntil: 'domcontentloaded' });

		await expect(
			page.getByRole('heading', { level: 1, name: 'How Validation Works' })
		).toBeVisible();
		await expect(page.getByRole('region', { name: 'Validation List' })).toBeVisible();
	});
});
