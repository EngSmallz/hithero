import { expect, test } from '@playwright/test';
import { installAuthenticatedSession } from '$lib/test/session';

test.describe('/login', () => {
	test('renders the login form and account links', async ({ page }) => {
		await page.goto('/login', { waitUntil: 'domcontentloaded' });

		await expect(
			page.getByRole('heading', { level: 1, name: 'Log In to Your Account' })
		).toBeVisible();
		await expect(page.getByLabel(/^Email/)).toBeVisible();
		await expect(page.getByLabel(/^Password/)).toBeVisible();
		await expect(page.getByRole('button', { name: 'Submit' })).toBeVisible();
		await expect(page.getByRole('link', { name: 'Forgot Password' })).toHaveAttribute(
			'href',
			'/forgot'
		);
		await expect(page.getByRole('link', { name: 'Register' })).toHaveAttribute('href', '/register');
	});

	test('opens mobile navigation', async ({ page }) => {
		await page.setViewportSize({ width: 390, height: 844 });
		await page.goto('/login', { waitUntil: 'domcontentloaded' });

		await page.getByRole('button', { name: 'Open navigation' }).click();

		const mobileNav = page.getByRole('navigation', { name: 'Mobile' });
		await expect(mobileNav).toBeVisible();
		await expect(mobileNav.getByRole('link', { name: 'Donate' })).toBeVisible();
		await expect(mobileNav.getByRole('link', { name: 'Sign Up' })).toBeVisible();
	});

	test('shows the backend message for invalid credentials', async ({ page }) => {
		await page.route('**/profile/login/', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify({ message: 'Invalid login credentials.' })
			});
		});

		await page.goto('/login', { waitUntil: 'domcontentloaded' });
		await page.getByLabel(/^Email/).fill('teacher@example.test');
		await page.getByLabel(/^Password/).fill('wrong-password');
		await page.getByRole('button', { name: 'Submit' }).click();

		await expect(page.getByRole('status')).toContainText('Invalid login credentials.');
		await expect(page).toHaveURL('/login');
	});

	test('routes teachers without a profile to profile creation', async ({ page }) => {
		await installAuthenticatedSession(page.context());
		await page.route('**/profile/login/', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify({
					message: 'Login successful as teacher',
					createCount: 0,
					role: 'teacher'
				})
			});
		});

		await page.route('**/api/profile/', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify({
					user_role: 'teacher',
					user_id: 12,
					user_email: 'teacher@example.test'
				})
			});
		});

		await page.goto('/login', { waitUntil: 'domcontentloaded' });
		await page.getByLabel(/^Email/).fill('teacher@example.test');
		await page.getByLabel(/^Password/).fill('valid-password');
		await page.getByRole('button', { name: 'Submit' }).click();

		await expect(page).toHaveURL('/profile/create');
	});
});
