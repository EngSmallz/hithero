import { expect, test, type Page } from '@playwright/test';

const recaptchaSiteKey = '6Lf9uiIqAAAAAMt19WMR4q0aO-JMqks9Du0yHHlL';

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

test.describe('/register', () => {
	test('renders the teacher registration form', async ({ page }) => {
		await page.goto('/register', { waitUntil: 'domcontentloaded' });

		await expect(page.getByRole('heading', { level: 1, name: 'User Registration' })).toBeVisible();
		await expect(
			page.getByRole('heading', { level: 2, name: 'Teacher Registration' })
		).toBeVisible();
		await expect(page.getByLabel(/^Name/)).toBeVisible();
		await expect(page.getByLabel(/^Email/)).toBeVisible();
		await expect(page.getByLabel(/^Phone Number/)).toBeVisible();
		await expect(page.getByLabel(/^Password/)).toBeVisible();
		await expect(page.getByLabel(/^Confirm Password/)).toBeVisible();
		await expect(page.getByRole('combobox', { name: /^State/ })).toBeVisible();
		await expect(page.getByRole('combobox', { name: /^County/ })).toBeVisible();
		await expect(page.getByRole('combobox', { name: /^School District/ })).toBeVisible();
		await expect(page.getByRole('combobox', { name: /^School required$/ })).toBeVisible();
		await expect(page.getByLabel('I have read the Terms and Conditions')).toBeVisible();
		await expect(page.locator('.g-recaptcha')).toHaveAttribute('data-sitekey', recaptchaSiteKey);
	});

	test('opens the terms dialog', async ({ page }) => {
		await page.goto('/register', { waitUntil: 'domcontentloaded' });

		await page.getByRole('button', { name: 'Open Terms' }).click();

		const dialog = page.getByRole('dialog', { name: 'Terms and Conditions' });
		await expect(dialog).toBeVisible();
		await expect(dialog.locator('iframe')).toHaveAttribute('src', '/terms');

		await page.getByRole('button', { name: 'Close' }).click();
		await expect(dialog).toBeHidden();
	});

	test('opens mobile navigation', async ({ page }) => {
		await page.setViewportSize({ width: 390, height: 844 });
		await page.goto('/register', { waitUntil: 'domcontentloaded' });

		await page.getByRole('button', { name: 'Open navigation' }).click();

		const mobileNav = page.getByRole('navigation', { name: 'Mobile' });
		await expect(mobileNav).toBeVisible();
		await expect(mobileNav.getByRole('link', { name: 'Donate' })).toBeVisible();
		await expect(mobileNav.getByRole('link', { name: 'Login' })).toBeVisible();
	});

	test('loads dependent county choices when a state is selected', async ({ page }) => {
		await page.route('**/api/get_counties/WA', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify(['King'])
			});
		});

		await page.goto('/register', { waitUntil: 'domcontentloaded' });
		await addSelectOption(page, /^State/, 'WA');

		await page.getByRole('combobox', { name: /^State/ }).selectOption('WA');

		await expect(page.getByRole('combobox', { name: /^County/ })).toContainText('King');
	});
});
