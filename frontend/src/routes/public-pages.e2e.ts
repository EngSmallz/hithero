import { expect, test } from '@playwright/test';

const publicPages = [
	{
		path: '/',
		title: 'Homeroom Heroes - Support Teachers',
		canonical: 'https://www.helpteachers.net/',
		heading: 'Support Teachers, Empower Futures!',
		description: /Connect with teachers/
	},
	{
		path: '/teachers',
		title: 'Homeroom Heroes - Find Teachers',
		canonical: 'https://www.helpteachers.net/teachers',
		heading: 'Find a Teacher',
		description: /Search for teachers/
	},
	{
		path: '/contact',
		title: 'Homeroom Heroes - Contact Us',
		canonical: 'https://www.helpteachers.net/contact',
		heading: 'Contact Us',
		description: /Contact Homeroom Heroes/
	},
	{
		path: '/register',
		title: 'Homeroom Heroes - Register',
		canonical: 'https://www.helpteachers.net/register',
		heading: 'User Registration',
		description: /Register as an educator/
	},
	{
		path: '/login',
		title: 'Homeroom Heroes - Login',
		canonical: 'https://www.helpteachers.net/login',
		heading: 'Log In to Your Account',
		description: /Log in to your Homeroom Heroes account/
	},
	{
		path: '/forgot',
		title: 'Homeroom Heroes - Forgot Password',
		canonical: 'https://www.helpteachers.net/forgot',
		heading: 'Forgot Your Password?',
		description: /Request password reset instructions/
	},
	{
		path: '/reset-password',
		title: 'Reset Password - Homeroom Heroes',
		canonical: 'https://www.helpteachers.net/reset-password',
		heading: 'Reset Your Password',
		description: /Reset your Homeroom Heroes account password/
	},
	{
		path: '/forum',
		title: 'Homeroom Heroes - Forum Discussions',
		canonical: 'https://www.helpteachers.net/forum',
		heading: "The Teachers' Lounge",
		description: /teacher forum discussions/
	},
	{
		path: '/partners',
		title: 'Homeroom Heroes - Sponsors and Thank You',
		canonical: 'https://www.helpteachers.net/partners',
		heading: 'Thank You to Our Partners',
		description: /radio, event, and financial partners/
	},
	{
		path: '/terms',
		title: 'Terms and Conditions - Homeroom Heroes',
		canonical: 'https://www.helpteachers.net/terms',
		heading: 'Terms and Conditions',
		description: /charitable contributions/
	},
	{
		path: '/wishlist-setup',
		title: 'Steps to Setup Wishlist - Homeroom Heroes',
		canonical: 'https://www.helpteachers.net/wishlist-setup',
		heading: 'Steps to Setup Wishlist',
		description: /Amazon classroom wishlist/
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
			await expect(page.locator('body')).not.toContainText('/pages/');
		});
	}
});
