import { expect, test } from '@playwright/test';

test.describe('/about', () => {
	test('renders visible about content', async ({ page }) => {
		await page.goto('/about');

		await expect(page.getByRole('heading', { level: 1, name: 'About Us' })).toBeVisible();
		await expect(page.getByRole('heading', { name: 'Our Mission' })).toBeVisible();
		await expect(page.getByText('501(c) registered charity')).toBeVisible();
		await expect(page.getByRole('heading', { name: 'Meet the Team' })).toBeVisible();
		await expect(page.getByRole('heading', { name: 'Justin Brundage' })).toBeVisible();
	});

	test('sets title, meta description, canonical, and Open Graph metadata', async ({ page }) => {
		await page.goto('/about');

		await expect(page).toHaveTitle('Homeroom Heroes - About Us');
		await expect(page.locator('meta[name="description"]')).toHaveAttribute(
			'content',
			/Learn about Homeroom Heroes/
		);
		await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
			'href',
			'https://www.helpteachers.net/about'
		);
		await expect(page.locator('meta[property="og:title"]')).toHaveAttribute(
			'content',
			'Homeroom Heroes - About Us'
		);
		await expect(page.locator('meta[property="og:url"]')).toHaveAttribute(
			'content',
			'https://www.helpteachers.net/about'
		);
	});

	test('opens mobile navigation', async ({ page }) => {
		await page.setViewportSize({ width: 390, height: 844 });
		await page.goto('/about');

		await page.getByRole('button', { name: 'Open navigation' }).click();

		const mobileNav = page.getByRole('navigation', { name: 'Mobile primary' });
		await expect(mobileNav.getByRole('link', { name: 'Donate' })).toBeVisible();
		await expect(mobileNav.getByRole('link', { name: 'Contact' })).toBeVisible();
		await expect(page.getByRole('button', { name: 'Close navigation' })).toBeVisible();
	});
});
