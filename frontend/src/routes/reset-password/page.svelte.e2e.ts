import { expect, test } from '@playwright/test';

test.describe('/reset-password', () => {
	test('shows an invalid link state when the token is missing', async ({ page }) => {
		await page.goto('/reset-password', { waitUntil: 'domcontentloaded' });

		await expect(
			page.getByRole('heading', { level: 1, name: 'Reset Your Password' })
		).toBeVisible();
		await expect(page.getByRole('heading', { name: 'Invalid Reset Link' })).toBeVisible();
		await expect(page.getByText('This password reset link is missing')).toBeVisible();
		await expect(page.getByRole('link', { name: 'Back to Login' })).toHaveAttribute(
			'href',
			'/login'
		);
		await expect(page.getByRole('link', { name: 'Request New Link' })).toHaveAttribute(
			'href',
			'/forgot'
		);
	});

	test('renders the reset form when a token is present', async ({ page }) => {
		await page.goto('/reset-password?token=reset-token-123', { waitUntil: 'domcontentloaded' });

		await expect(page.getByLabel(/^New Password/)).toBeVisible();
		await expect(page.getByLabel(/^Confirm New Password/)).toBeVisible();
		await expect(page.locator('input[name="token"]')).toHaveValue('reset-token-123');
		await expect(page.getByRole('button', { name: 'Reset Password' })).toBeVisible();
		await expect(page.getByRole('link', { name: 'Back to Login' })).toHaveAttribute(
			'href',
			'/login'
		);
	});

	test('opens mobile navigation', async ({ page }) => {
		await page.setViewportSize({ width: 390, height: 844 });
		await page.goto('/reset-password?token=reset-token-123', { waitUntil: 'domcontentloaded' });

		await page.getByRole('button', { name: 'Open navigation' }).click();

		const mobileNav = page.getByRole('navigation', { name: 'Mobile primary' });
		await expect(mobileNav).toBeVisible();
		await expect(mobileNav.getByRole('link', { name: 'Donate' })).toBeVisible();
		await expect(mobileNav.getByRole('link', { name: 'Login' })).toBeVisible();
	});

	test('shows a password mismatch message before posting', async ({ page }) => {
		await page.goto('/reset-password?token=reset-token-123', { waitUntil: 'domcontentloaded' });
		await page.getByLabel(/^New Password/).fill('one-password');
		await page.getByLabel(/^Confirm New Password/).fill('another-password');
		await page.getByRole('button', { name: 'Reset Password' }).click();

		await expect(page.getByRole('status')).toContainText('Passwords do not match.');
	});

	test('shows the backend invalid token message', async ({ page }) => {
		await page.route('**/profile/reset_password/', async (route) => {
			await route.fulfill({
				status: 400,
				contentType: 'application/json',
				body: JSON.stringify({ detail: 'Invalid or expired reset token.' })
			});
		});

		await page.goto('/reset-password?token=expired-token', { waitUntil: 'domcontentloaded' });
		await page.getByLabel(/^New Password/).fill('matching-password');
		await page.getByLabel(/^Confirm New Password/).fill('matching-password');
		await page.getByRole('button', { name: 'Reset Password' }).click();

		await expect(page.getByRole('alert')).toContainText('Invalid or expired reset token.');
	});

	test('displays the success message returned by the backend', async ({ page }) => {
		const backendMessage = 'Password reset successfully. You can now log in.';

		await page.route('**/profile/reset_password/', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify({ message: backendMessage })
			});
		});

		await page.goto('/reset-password?token=reset-token-123', { waitUntil: 'domcontentloaded' });
		await page.getByLabel(/^New Password/).fill('matching-password');
		await page.getByLabel(/^Confirm New Password/).fill('matching-password');
		await page.getByRole('button', { name: 'Reset Password' }).click();

		await expect(page.getByRole('heading', { name: 'Password Reset!' })).toBeVisible();
		await expect(page.getByRole('status')).toContainText(backendMessage);
		await expect(page.getByRole('link', { name: 'Go to Login' })).toHaveAttribute('href', '/login');
	});
});
