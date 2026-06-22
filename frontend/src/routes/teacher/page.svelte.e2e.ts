import { expect, test, type Page } from '@playwright/test';
import { installAuthenticatedSession } from '$lib/test/session';

const teacherProfile = {
	state: 'Washington',
	county: 'King',
	district: 'Seattle Public Schools',
	school: 'Evergreen Elementary',
	name: 'Avery Adams',
	wishlist_url: 'https://example.com/wishlist',
	about_me: 'I build a classroom where students can practice curiosity every day.',
	image_data: null
};

async function installTeacherInfoStub(page: Page) {
	await page.route('**/api/get_teacher_info/', async (route) => {
		await route.fulfill({
			contentType: 'application/json',
			body: JSON.stringify(teacherProfile)
		});
	});
}

async function installAnonymousProfileStub(page: Page) {
	await page.route('**/api/profile/', async (route) => {
		await route.fulfill({
			status: 404,
			contentType: 'application/json',
			body: JSON.stringify({ detail: 'No user logged in.' })
		});
	});
}

async function installOwnerProfileStub(page: Page) {
	await installAuthenticatedSession(page.context());
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
	await page.route('**/api/check_access_teacher/', async (route) => {
		await route.fulfill({
			contentType: 'application/json',
			body: JSON.stringify({ status: 'success', message: 'Access granted' })
		});
	});
}

test.describe('/teacher', () => {
	test('renders mocked backend profile data for public visitors', async ({ page }) => {
		await installAnonymousProfileStub(page);
		await installTeacherInfoStub(page);

		await page.goto('/teacher', { waitUntil: 'domcontentloaded' });

		await expect(page.getByRole('heading', { level: 1, name: 'Avery Adams' })).toBeVisible();
		await expect(page.getByText('School: Evergreen Elementary')).toBeVisible();
		await expect(page.getByText('Location: King, Washington')).toBeVisible();
		await expect(
			page.getByText('I build a classroom where students can practice curiosity every day.')
		).toBeVisible();
		await expect(page.getByRole('link', { name: 'View Wishlist' })).toHaveAttribute(
			'href',
			'https://example.com/wishlist'
		);
		await expect(page.getByRole('button', { name: 'Share Page' })).toBeVisible();
		await expect(page.getByRole('link', { name: 'Edit Info' })).toHaveCount(0);
	});

	test('shows owner-only controls for the matching teacher', async ({ page }) => {
		await installOwnerProfileStub(page);
		await installTeacherInfoStub(page);

		await page.goto('/teacher', { waitUntil: 'domcontentloaded' });

		await expect(page.getByRole('button', { name: 'Update Image' })).toBeVisible();
		await expect(page.getByRole('link', { name: 'Edit Info' })).toHaveAttribute(
			'href',
			'/profile/edit'
		);
		await expect(page.getByRole('link', { name: 'Update Password' })).toHaveAttribute(
			'href',
			'/update-password'
		);
	});

	test('does not show owner controls to unauthenticated visitors', async ({ page }) => {
		await installAnonymousProfileStub(page);
		await installTeacherInfoStub(page);

		await page.goto('/teacher', { waitUntil: 'domcontentloaded' });

		await expect(page.getByRole('heading', { level: 1, name: 'Avery Adams' })).toBeVisible();
		await expect(page.getByRole('button', { name: 'Update Image' })).toHaveCount(0);
		await expect(page.getByRole('link', { name: 'Edit Info' })).toHaveCount(0);
		await expect(page.getByRole('link', { name: 'Update Password' })).toHaveCount(0);
	});

	test('opens mobile navigation', async ({ page }) => {
		await installAnonymousProfileStub(page);
		await installTeacherInfoStub(page);
		await page.setViewportSize({ width: 390, height: 844 });

		await page.goto('/teacher', { waitUntil: 'domcontentloaded' });
		await page.getByRole('button', { name: 'Open navigation' }).click();

		const mobileNav = page.getByRole('navigation', { name: 'Mobile primary' });
		await expect(mobileNav).toBeVisible();
		await expect(mobileNav.getByRole('link', { name: 'Donate' })).toBeVisible();
		await expect(mobileNav.getByRole('link', { name: 'Login' })).toBeVisible();
	});

	test('shows a useful message when teacher data is unavailable', async ({ page }) => {
		await installAnonymousProfileStub(page);
		await page.route('**/api/get_teacher_info/', async (route) => {
			await route.fulfill({
				status: 404,
				contentType: 'application/json',
				body: JSON.stringify({ detail: 'Teacher not found' })
			});
		});

		await page.goto('/teacher', { waitUntil: 'domcontentloaded' });

		await expect(page.getByRole('alert')).toContainText('Teacher profile could not be loaded');
	});
});
