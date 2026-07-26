import { expect, test } from '@playwright/test';

const safeResetMessage = 'If an account exists, a reset link will be sent to your email.';

test.describe('/forgot', () => {
	test('renders the forgot password form and account links', async ({ page }) => {
		await page.goto('/forgot', { waitUntil: 'domcontentloaded' });

		await expect(
			page.getByRole('heading', { level: 1, name: 'Forgot Your Password?' })
		).toBeVisible();
		await expect(page.getByLabel(/^Email/)).toBeVisible();
		await expect(page.getByRole('button', { name: 'Submit' })).toBeVisible();
		await expect(page.getByRole('link', { name: 'Back to Login' })).toHaveAttribute(
			'href',
			'/login'
		);
		await expect(page.getByRole('link', { name: 'Register' })).toHaveAttribute('href', '/register');
	});

	test('opens mobile navigation', async ({ page }) => {
		await page.setViewportSize({ width: 390, height: 844 });
		await page.goto('/forgot', { waitUntil: 'domcontentloaded' });
		await page.waitForLoadState('networkidle');

		await page.getByRole('button', { name: 'Open navigation' }).click();

		const mobileNav = page.getByRole('navigation', { name: 'Mobile primary' });
		await expect(mobileNav).toBeVisible();
		await expect(mobileNav.getByRole('link', { name: 'Donate' })).toBeVisible();
		await expect(mobileNav.getByRole('link', { name: 'Login' })).toBeVisible();
	});

	test('shows the safe backend message for an unknown email', async ({ page }) => {
		await page.route('**/profile/forgot_password/', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify({ message: safeResetMessage })
			});
		});

		await page.goto('/forgot', { waitUntil: 'domcontentloaded' });
		await page.waitForLoadState('networkidle');
		await page.getByLabel(/^Email/).fill('unknown@example.test');
		await page.getByRole('button', { name: 'Submit' }).click();

		await expect(page.getByRole('status')).toContainText(safeResetMessage);
		await expect(page).toHaveURL('/forgot');
	});

	test('displays the success message returned by the backend', async ({ page }) => {
		const backendMessage = 'Password reset request accepted.';

		await page.route('**/profile/forgot_password/', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify({ message: backendMessage })
			});
		});

		await page.goto('/forgot', { waitUntil: 'domcontentloaded' });
		await page.waitForLoadState('networkidle');
		await page.getByLabel(/^Email/).fill('teacher@example.test');
		await page.getByRole('button', { name: 'Submit' }).click();

		await expect(page.getByRole('status')).toContainText(backendMessage);
	});
});
