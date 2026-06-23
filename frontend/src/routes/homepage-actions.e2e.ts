import { expect, test } from '@playwright/test';

const teacher = {
	name: 'Avery Adams',
	state: 'Washington',
	county: 'King',
	district: 'Seattle Public Schools',
	school: 'Evergreen Elementary',
	image_data: null
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
		await expect(page.getByText('Avery Adams')).toBeVisible();
		await expect(page.getByRole('link', { name: 'View Teacher of the Day' })).toHaveAttribute(
			'href',
			'/teacher'
		);
	});

	test('selects and reveals a random teacher', async ({ page }) => {
		await page.route('**/api/random_teacher/', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify({ ...teacher, name: 'Random Riley' })
			});
		});
		await page.goto('/', { waitUntil: 'domcontentloaded' });

		await page.getByRole('button', { name: 'Find Random Teacher' }).click();

		await expect(page.getByText('Random Riley')).toBeVisible();
		await expect(page.getByRole('link', { name: 'View Random Teacher' })).toHaveAttribute(
			'href',
			'/teacher'
		);
	});
});
