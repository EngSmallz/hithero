import { expect, test } from '@playwright/test';
import { installAuthenticatedSession } from '$lib/test/session';

const teacher = {
	name: 'Avery Adams',
	state: 'Washington',
	county: 'King',
	district: 'Seattle Public Schools',
	school: 'Evergreen Elementary',
	image_data: null,
	url_id: 'avery-adams'
};

test.describe('homepage teacher actions', () => {
	test.beforeEach(async ({ page }) => {
		await page.route('**/spotlight/teacher', async (route) => {
			await route.fulfill({ contentType: 'application/json', body: JSON.stringify(teacher) });
		});
		await page.route('**/promo/get_promo_info/', async (route) => {
			await route.fulfill({ contentType: 'application/json', body: '{}' });
		});
	});

	test('renders the Teacher of the Day from FastAPI', async ({ page }) => {
		await page.goto('/', { waitUntil: 'domcontentloaded' });

		await expect(page.getByRole('heading', { name: 'Teacher of the Day' })).toBeVisible();
		await expect(page.getByText('Avery Adams').first()).toBeVisible();
		await expect(page.getByRole('link', { name: 'View Teacher of the Day' })).toHaveAttribute(
			'href',
			'/teacher/avery-adams'
		);
		await page.getByRole('link', { name: 'View Teacher of the Day' }).click();
		await expect(page).toHaveURL('/teacher/avery-adams');
		await expect(page.getByRole('heading', { level: 1, name: 'Avery Adams' })).toBeVisible();
	});

	test('selects and reveals a random teacher', async ({ page }) => {
		await page.route('**/api/random_teacher/', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify({ ...teacher, name: 'Random Riley', url_id: 'random-riley' })
			});
		});
		await page.goto('/', { waitUntil: 'domcontentloaded' });

		await page.getByRole('button', { name: 'Find Random Teacher' }).click();

		await expect(page.getByText('Random Riley')).toBeVisible();
		await expect(page.getByRole('link', { name: 'View Random Teacher' })).toHaveAttribute(
			'href',
			'/teacher/random-riley'
		);
		await page.getByRole('link', { name: 'View Random Teacher' }).click();
		await expect(page).toHaveURL('/teacher/random-riley');
		await expect(page.getByRole('heading', { level: 1, name: 'Random Riley' })).toBeVisible();
	});
});

test.describe('authenticated header logout', () => {
	test.beforeEach(async ({ page, context }) => {
		await installAuthenticatedSession(context);
		await page.goto('/', { waitUntil: 'domcontentloaded' });
		await expect(page.locator('[data-header-enhanced]')).toHaveAttribute(
			'data-header-enhanced',
			'true'
		);
	});

	test('posts logout and returns the header to its signed-out state', async ({ page }) => {
		await page.route('**/profile/logout/', async (route) => {
			expect(route.request().method()).toBe('POST');
			await route.fulfill({
				contentType: 'application/json',
				headers: { 'set-cookie': 'session=; Path=/; Max-Age=0; SameSite=Lax' },
				body: JSON.stringify({ message: 'Logged out successfully.' })
			});
		});

		await page.getByRole('button', { name: 'Logout' }).click();

		await expect(page).toHaveURL('/');
		await expect(page.getByRole('link', { name: 'Login' })).toBeVisible();
	});

	test('keeps the authenticated state and explains a logout failure', async ({ page }) => {
		await page.route('**/profile/logout/', async (route) => {
			await route.fulfill({
				status: 503,
				contentType: 'application/json',
				body: JSON.stringify({ detail: 'Logout unavailable.' })
			});
		});
		const dialogHandled = new Promise<void>((resolve) => {
			page.once('dialog', async (dialog) => {
				expect(dialog.message()).toBe('We could not log you out. Please try again.');
				await dialog.dismiss();
				resolve();
			});
		});

		await page.getByRole('button', { name: 'Logout' }).click();
		await dialogHandled;

		await expect(page.getByRole('button', { name: 'Logout' })).toBeVisible();
	});
});
