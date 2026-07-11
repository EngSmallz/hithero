import { expect, test } from '@playwright/test';

const publicPages = [
	{
		path: '/',
		title: 'Homeroom Heroes - Support Teachers',
		canonical: 'https://www.helpteachers.net/',
		heading: 'Support Teachers, Empower Futures!',
		description: /Connect with teachers/,
		robots: null
	},
	{
		path: '/teachers',
		title: 'Homeroom Heroes - Find Teachers',
		canonical: 'https://www.helpteachers.net/teachers',
		heading: 'Find a Teacher',
		description: /Search for teachers/,
		robots: null
	},
	{
		path: '/contact',
		title: 'Homeroom Heroes - Contact Us',
		canonical: 'https://www.helpteachers.net/contact',
		heading: 'Contact Us',
		description: /Contact Homeroom Heroes/,
		robots: null
	},
	{
		path: '/register',
		title: 'Homeroom Heroes - Register',
		canonical: 'https://www.helpteachers.net/register',
		heading: 'User Registration',
		description: /Register as an educator/,
		robots: null
	},
	{
		path: '/login',
		title: 'Homeroom Heroes - Login',
		canonical: 'https://www.helpteachers.net/login',
		heading: 'Log In to Your Account',
		description: /Log in to your Homeroom Heroes account/,
		robots: null
	},
	{
		path: '/forgot',
		title: 'Homeroom Heroes - Forgot Password',
		canonical: 'https://www.helpteachers.net/forgot',
		heading: 'Forgot Your Password?',
		description: /Request password reset instructions/,
		robots: null
	},
	{
		path: '/reset-password',
		title: 'Reset Password - Homeroom Heroes',
		canonical: 'https://www.helpteachers.net/reset-password',
		heading: 'Reset Your Password',
		description: /Reset your Homeroom Heroes account password/,
		robots: 'noindex, nofollow'
	},
	{
		path: '/partners',
		title: 'Homeroom Heroes - Sponsors and Thank You',
		canonical: 'https://www.helpteachers.net/partners',
		heading: 'Thank You to Our Partners',
		description: /radio, event, and financial partners/,
		robots: null
	},
	{
		path: '/terms',
		title: 'Terms and Conditions - Homeroom Heroes',
		canonical: 'https://www.helpteachers.net/terms',
		heading: 'Terms and Conditions',
		description: /charitable contributions/,
		robots: null
	},
	{
		path: '/wishlist-setup',
		title: 'Steps to Setup Wishlist - Homeroom Heroes',
		canonical: 'https://www.helpteachers.net/wishlist-setup',
		heading: 'Steps to Setup Wishlist',
		description: /Amazon classroom wishlist/,
		robots: null
	}
];

test.describe('static public pages', () => {
	for (const pageSpec of publicPages) {
		test(`${pageSpec.path} renders content and SEO metadata`, async ({ page }) => {
			await page.goto(pageSpec.path, { waitUntil: 'domcontentloaded' });

			await expect(page).toHaveTitle(pageSpec.title);
			await expect(page.getByRole('heading', { level: 1, name: pageSpec.heading })).toBeVisible();
			await expect(page.locator('meta[name="description"]')).toHaveAttribute(
				'content',
				pageSpec.description
			);
			await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
				'href',
				pageSpec.canonical
			);
			await expect(page.locator('meta[property="og:title"]')).toHaveAttribute(
				'content',
				pageSpec.title
			);
			await expect(page.locator('meta[property="og:description"]')).toHaveAttribute(
				'content',
				pageSpec.description
			);
			await expect(page.locator('meta[property="og:url"]')).toHaveAttribute(
				'content',
				pageSpec.canonical
			);
			await expect(page.locator('meta[property="og:image"]')).toHaveAttribute(
				'content',
				'https://www.helpteachers.net/images/logo_transparent.png'
			);
			if (pageSpec.robots) {
				await expect(page.locator('meta[name="robots"]')).toHaveAttribute(
					'content',
					pageSpec.robots
				);
			} else {
				await expect(page.locator('meta[name="robots"]')).toHaveCount(0);
			}
			await expect(page.locator('body')).not.toContainText('/pages/');
		});
	}

	for (const errorSpec of [
		{ path: '/403', status: 403, heading: 'Forbidden' },
		{ path: '/404', status: 404, heading: 'Page Does Not Exist' }
	]) {
		test(`${errorSpec.path} renders noindex error metadata`, async ({ page }) => {
			const response = await page.goto(errorSpec.path, { waitUntil: 'domcontentloaded' });

			expect(response?.status()).toBe(errorSpec.status);
			await expect(page.getByRole('heading', { level: 1, name: errorSpec.heading })).toBeVisible();
			await expect(page.locator('meta[name="robots"]')).toHaveAttribute(
				'content',
				'noindex, nofollow'
			);
		});
	}
});
