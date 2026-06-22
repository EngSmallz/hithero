import { expect, test } from '@playwright/test';
import { installAuthenticatedSession } from '$lib/test/session';

test.describe('/update-password', () => {
	test.beforeEach(async ({ context }) => {
		await installAuthenticatedSession(context);
	});

	test('redirects unauthenticated visitors to login before rendering', async ({
		page,
		context
	}) => {
		await context.clearCookies();
		await page.goto('/update-password', { waitUntil: 'domcontentloaded' });

		await expect(page).toHaveURL('/login?redirect=%2Fupdate-password');
	});
	test('renders the update password form', async ({ page }) => {
		await page.goto('/update-password', { waitUntil: 'domcontentloaded' });

		await expect(
			page.getByRole('heading', { level: 1, name: 'Update Your Password' })
		).toBeVisible();
		await expect(page.getByLabel(/^Old Password/)).toBeVisible();
		await expect(page.getByLabel(/^New Password/)).toBeVisible();
		await expect(page.getByLabel(/^Confirm New Password/)).toBeVisible();
		await expect(page.getByRole('button', { name: 'Submit' })).toBeVisible();
	});

	test('opens mobile navigation', async ({ page }) => {
		await page.setViewportSize({ width: 390, height: 844 });
		await page.goto('/update-password', { waitUntil: 'domcontentloaded' });

		await page.getByRole('button', { name: 'Open navigation' }).click();

		const mobileNav = page.getByRole('navigation', { name: 'Mobile primary' });
		await expect(mobileNav).toBeVisible();
		await expect(mobileNav.getByRole('link', { name: 'Donate' })).toBeVisible();
		await expect(mobileNav.getByRole('button', { name: 'Logout' })).toBeVisible();
	});

	test('shows backend validation messages without redirecting', async ({ page }) => {
		await page.route('**/profile/update_password/', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify({ message: 'Invalid old password' })
			});
		});

		await page.goto('/update-password', { waitUntil: 'domcontentloaded' });
		await page.getByLabel(/^Old Password/).fill('wrong-password');
		await page.getByLabel(/^New Password/).fill('new password');
		await page.getByLabel(/^Confirm New Password/).fill('new password');
		await page.getByRole('button', { name: 'Submit' }).click();

		await expect(page.getByRole('status')).toContainText('Invalid old password');
		await expect(page).toHaveURL('/update-password');
	});

	test('submits to FastAPI and returns to the teacher page on success', async ({ page }) => {
		await page.route('**/profile/update_password/', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify({ status: 'success', message: 'Password updated successfully' })
			});
		});
		await page.route('**/api/profile/', async (route) => {
			await route.fulfill({
				status: 404,
				contentType: 'application/json',
				body: JSON.stringify({ detail: 'No user logged in.' })
			});
		});
		await page.route('**/api/get_teacher_info/', async (route) => {
			await route.fulfill({
				status: 404,
				contentType: 'application/json',
				body: JSON.stringify({ detail: 'Teacher not found' })
			});
		});

		await page.goto('/update-password', { waitUntil: 'domcontentloaded' });
		await page.getByLabel(/^Old Password/).fill('old password');
		await page.getByLabel(/^New Password/).fill('new password');
		await page.getByLabel(/^Confirm New Password/).fill('new password');
		await page.getByRole('button', { name: 'Submit' }).click();

		await expect(page).toHaveURL('/teacher');
	});
});
