import { expect, test, type Page } from '@playwright/test';
import { installAuthenticatedSession } from '$lib/test/session';

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

async function installTeacherProfileStub(page: Page) {
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
}

async function addSchoolSelections(page: Page) {
	const stateSelect = page.getByRole('combobox', { name: /^State/ });
	await addSelectOption(page, /^State/, 'WA');
	await expect(stateSelect).toContainText('WA');
	await stateSelect.selectOption('WA');
	await expect(page.getByRole('combobox', { name: /^County/ })).toContainText('King');
	await page.getByRole('combobox', { name: /^County/ }).selectOption('King');
	await expect(page.getByRole('combobox', { name: /^School District/ })).toContainText(
		'Seattle Public Schools'
	);
	await page
		.getByRole('combobox', { name: /^School District/ })
		.selectOption('Seattle Public Schools');
	await expect(page.getByRole('combobox', { name: /^School required$/ })).toContainText(
		'Evergreen Elementary'
	);
	await page
		.getByRole('combobox', { name: /^School required$/ })
		.selectOption('Evergreen Elementary');
}

test.describe('/profile/create', () => {
	test('renders the teacher profile creation form for teachers', async ({ page }) => {
		await installTeacherProfileStub(page);

		await page.goto('/profile/create', { waitUntil: 'domcontentloaded' });

		await expect(
			page.getByRole('heading', { level: 1, name: 'Create Teacher Profile' })
		).toBeVisible();
		await expect(page.getByLabel(/^Full Name/)).toBeVisible();
		await expect(page.getByRole('combobox', { name: /^State/ })).toBeVisible();
		await expect(page.getByRole('combobox', { name: /^County/ })).toBeVisible();
		await expect(page.getByRole('combobox', { name: /^School District/ })).toBeVisible();
		await expect(page.getByRole('combobox', { name: /^School required$/ })).toBeVisible();
		await expect(page.getByLabel(/^About Me/)).toBeVisible();
		await expect(page.getByText('500 characters remaining')).toBeVisible();
		await expect(page.getByLabel(/^Amazon Wishlist URL/)).toBeVisible();
		await expect(page.getByRole('button', { name: 'Submit' })).toBeVisible();
		await expect(page.locator('meta[name="robots"]')).toHaveAttribute(
			'content',
			'noindex, nofollow'
		);
	});

	test('redirects unauthenticated visitors to login before rendering', async ({ page }) => {
		await page.goto('/profile/create', { waitUntil: 'domcontentloaded' });

		await expect(page).toHaveURL('/login?redirect=%2Fprofile%2Fcreate');
	});

	test('opens mobile navigation', async ({ page }) => {
		await installTeacherProfileStub(page);
		await page.setViewportSize({ width: 390, height: 844 });
		await page.goto('/profile/create', { waitUntil: 'domcontentloaded' });

		await page.getByRole('button', { name: 'Open navigation' }).click();

		const mobileNav = page.getByRole('navigation', { name: 'Mobile primary' });
		await expect(mobileNav).toBeVisible();
		await expect(mobileNav.getByRole('link', { name: 'Donate' })).toBeVisible();
		await expect(mobileNav.getByRole('button', { name: 'Logout' })).toBeVisible();
	});

	test('loads dependent county choices when a state is selected', async ({ page }) => {
		await installTeacherProfileStub(page);
		await page.route('**/api/get_counties/WA', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify(['King'])
			});
		});

		await page.goto('/profile/create', { waitUntil: 'domcontentloaded' });
		await addSelectOption(page, /^State/, 'WA');

		await page.getByRole('combobox', { name: /^State/ }).selectOption('WA');

		await expect(page.getByRole('combobox', { name: /^County/ })).toContainText('King');
	});

	test('opens wishlist setup help', async ({ page }) => {
		await installTeacherProfileStub(page);
		await page.goto('/profile/create', { waitUntil: 'domcontentloaded' });

		await page.getByRole('button', { name: 'How to Get Link' }).click();

		const dialog = page.getByRole('dialog', { name: 'Wishlist setup' });
		await expect(dialog).toBeVisible();
		await expect(dialog.locator('iframe')).toHaveAttribute('src', '/wishlist-setup');

		await page.getByRole('button', { name: 'Close' }).click();
		await expect(dialog).toBeHidden();
	});

	test('submits profile creation and displays the backend message', async ({ page }) => {
		await installTeacherProfileStub(page);
		await page.route('**/api/get_counties/WA', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify(['King'])
			});
		});
		await page.route('**/api/get_districts/WA/King', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify(['Seattle Public Schools'])
			});
		});
		await page.route('**/api/get_schools/WA/King/Seattle%20Public%20Schools', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify(['Evergreen Elementary'])
			});
		});
		await page.route('**/profile/create_teacher_profile/', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify({
					message: 'Teacher created successfully',
					role: 'teacher'
				})
			});
		});

		await page.goto('/profile/create', { waitUntil: 'load' });
		await page.waitForLoadState('networkidle');
		await addSchoolSelections(page);
		await page.getByLabel(/^Full Name/).fill('Integration Teacher');
		await page.getByLabel(/^About Me/).fill('I help students build durable skills.');
		await page.getByLabel(/^Amazon Wishlist URL/).fill('https://example.com/wishlist');
		await page.getByRole('button', { name: 'Submit' }).click();

		await expect(page.getByRole('status')).toContainText('Teacher created successfully');
		await expect(page.getByRole('button', { name: 'View My Page' })).toBeVisible();
	});
});
