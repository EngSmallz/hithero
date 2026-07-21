import { expect, test, type Page } from '@playwright/test';
import { installAuthenticatedSession } from '$lib/test/session';

async function installAdminSession(page: Page) {
	await installAuthenticatedSession(page.context(), 'admin');
}

async function addSelectOption(page: Page, label: RegExp, value: string) {
	await page.getByRole('combobox', { name: label }).evaluate((select, optionValue) => {
		if (!(select instanceof HTMLSelectElement)) {
			return;
		}

		if (![...select.options].some((option) => option.value === optionValue)) {
			select.add(new Option(optionValue, optionValue));
		}
	}, value);
}

async function routeSchoolChoices(page: Page) {
	await page.route('**/api/index_counties/Washington', async (route) => {
		await route.fulfill({
			contentType: 'application/json',
			body: JSON.stringify(['King'])
		});
	});
	await page.route('**/api/index_districts/Washington/King', async (route) => {
		await route.fulfill({
			contentType: 'application/json',
			body: JSON.stringify(['Seattle Public Schools'])
		});
	});
	await page.route(
		'**/api/index_schools/Washington/King/Seattle%20Public%20Schools',
		async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify(['Evergreen Elementary'])
			});
		}
	);
}

async function addReportSelections(page: Page) {
	await addSelectOption(page, /^State/, 'Washington');
	await page.getByRole('combobox', { name: /^State/ }).selectOption('Washington');
	await expect(page.getByRole('combobox', { name: /^County/ })).toContainText('King');
	await page.getByRole('combobox', { name: /^County/ }).selectOption('King');
	await expect(page.getByRole('combobox', { name: /^School District/ })).toContainText(
		'Seattle Public Schools'
	);
	await page
		.getByRole('combobox', { name: /^School District/ })
		.selectOption('Seattle Public Schools');
	await expect(page.getByRole('combobox', { name: /^School$/ })).toContainText(
		'Evergreen Elementary'
	);
	await page.getByRole('combobox', { name: /^School$/ }).selectOption('Evergreen Elementary');
}

test.describe('/admin', () => {
	test('redirects unauthenticated visitors to login before rendering', async ({ page }) => {
		await page.goto('/admin', { waitUntil: 'domcontentloaded' });

		await expect(page).toHaveURL('/login?redirect=%2Fadmin');
	});

	test('returns 403 for authenticated non-admin users', async ({ page, context }) => {
		await installAuthenticatedSession(context, 'teacher');

		const response = await page.goto('/admin', { waitUntil: 'domcontentloaded' });

		expect(response?.status()).toBe(403);
		await expect(page.getByRole('heading', { level: 1, name: 'Forbidden' })).toBeVisible();
	});

	test('renders administrator tools for admins', async ({ page }) => {
		await installAdminSession(page);

		await page.goto('/admin', { waitUntil: 'domcontentloaded' });

		await expect(page.getByRole('heading', { level: 1, name: 'Admin Panel' })).toBeVisible();
		await expect(
			page.getByRole('heading', { level: 2, name: 'Get Teacher Contact Info' })
		).toBeVisible();
		await expect(page.getByRole('combobox', { name: /^State/ })).toBeVisible();
		await expect(page.getByRole('combobox', { name: /^County/ })).toBeVisible();
		await expect(page.getByRole('combobox', { name: /^School District/ })).toBeVisible();
		await expect(page.getByRole('combobox', { name: /^School$/ })).toBeVisible();
		await expect(
			page.getByRole('heading', { level: 2, name: 'Delete User Account' })
		).toBeVisible();
		await expect(page.getByLabel(/^Target User Email/)).toBeVisible();
		await expect(page.getByLabel(/^Admin Secret Key/)).toBeVisible();
		await expect(page.locator('meta[name="robots"]')).toHaveAttribute(
			'content',
			'noindex, nofollow'
		);
	});

	test('loads dependent school choices from FastAPI as filters change', async ({ page }) => {
		await installAdminSession(page);
		await routeSchoolChoices(page);

		await page.goto('/admin', { waitUntil: 'domcontentloaded' });
		await page.waitForLoadState('networkidle');
		await addSelectOption(page, /^State/, 'Washington');

		await page.getByRole('combobox', { name: /^State/ }).selectOption('Washington');
		await expect(page.getByRole('combobox', { name: /^County/ })).toContainText('King');
		await page.getByRole('combobox', { name: /^County/ }).selectOption('King');
		await expect(page.getByRole('combobox', { name: /^School District/ })).toContainText(
			'Seattle Public Schools'
		);
		await page
			.getByRole('combobox', { name: /^School District/ })
			.selectOption('Seattle Public Schools');
		await expect(page.getByRole('combobox', { name: /^School$/ })).toContainText(
			'Evergreen Elementary'
		);
	});

	test('submits teacher report generation and shows backend message', async ({ page }) => {
		await installAdminSession(page);
		await routeSchoolChoices(page);
		await page.route('**/admin/generate_teacher_report/', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify({ message: 'Teacher report sent.' })
			});
		});

		await page.goto('/admin', { waitUntil: 'domcontentloaded' });
		await addReportSelections(page);
		await page.getByRole('button', { name: 'Get Info' }).click();

		await expect(page.getByRole('status')).toContainText('Teacher report sent.');
	});

	test('confirms and submits user deletion to FastAPI', async ({ page }) => {
		await installAdminSession(page);
		await page.route('**/profile/delete/', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify({ message: 'User deleted.' })
			});
		});
		page.on('dialog', async (dialog) => {
			expect(dialog.message()).toContain('delete user: old-user@example.test');
			await dialog.accept();
		});

		await page.goto('/admin', { waitUntil: 'domcontentloaded' });
		await page.getByLabel(/^Target User Email/).fill('old-user@example.test');
		await page.getByLabel(/^Admin Secret Key/).fill('admin-secret');
		await page.getByRole('button', { name: 'Permanently Delete Account' }).click();

		await expect(page.getByRole('status')).toContainText('User deleted.');
	});
});
