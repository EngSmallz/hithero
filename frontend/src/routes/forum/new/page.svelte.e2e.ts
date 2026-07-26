import { expect, test } from '@playwright/test';
import { installAuthenticatedSession } from '$lib/test/session';

test.describe('/forum/new', () => {
	test('redirects unauthenticated visitors to login before rendering', async ({ page }) => {
		await page.goto('/forum/new', { waitUntil: 'domcontentloaded' });

		await expect(page).toHaveURL('/login?redirect=%2Fforum%2Fnew');
	});

	test('renders the authenticated new discussion form', async ({ page, context }) => {
		await installAuthenticatedSession(context);
		await page.goto('/forum/new', { waitUntil: 'domcontentloaded' });

		await expect(
			page.getByRole('heading', { level: 1, name: 'Create a New Discussion' })
		).toBeVisible();
		await expect(page.getByLabel(/^Title/)).toBeVisible();
		await expect(page.getByLabel(/^Content/)).toBeVisible();
		await expect(page.getByRole('link', { name: 'Back to Forum' })).toHaveAttribute(
			'href',
			'/forum'
		);
		await expect(page.locator('meta[name="robots"]')).toHaveAttribute(
			'content',
			'noindex, nofollow'
		);
	});

	test('submits a new discussion to FastAPI and opens the created post', async ({
		page,
		context
	}) => {
		await installAuthenticatedSession(context);
		await page.route('**/forum/create_post', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify({
					id: 501,
					title: 'New classroom discussion',
					content: 'This new post was created from SvelteKit.',
					user_id: 12,
					created_at: '2026-06-23T12:00:00',
					upvote_count: 0,
					comment_count: 0
				})
			});
		});

		await page.goto('/forum/new', { waitUntil: 'domcontentloaded' });
		await page.getByLabel(/^Title/).fill('New classroom discussion');
		await page.getByLabel(/^Content/).fill('This new post was created from SvelteKit.');
		await page.getByRole('button', { name: 'Create Post' }).click();

		await expect(page).toHaveURL('/forum/post?id=501');
	});

	test.describe('without JavaScript', () => {
		test.use({ javaScriptEnabled: false });

		test('submits through the SvelteKit fallback instead of exposing backend JSON', async ({
			page,
			context
		}, testInfo) => {
			await installAuthenticatedSession(context);
			const uniqueTitle = `No JS classroom discussion ${testInfo.workerIndex}-${Date.now()}`;

			await page.goto('/forum/new', { waitUntil: 'domcontentloaded' });
			await page.getByLabel(/^Title/).fill(uniqueTitle);
			await page
				.getByLabel(/^Content/)
				.fill('This native submission should stay on a Svelte-owned page.');
			await page.getByRole('button', { name: 'Create Post' }).click();

			await expect(page).toHaveURL('/forum/new');
			await expect(page.getByRole('status')).toContainText('Discussion created.');
			await expect(page.getByText(uniqueTitle)).toBeVisible();

			const openDiscussionLink = page.getByRole('link', { name: 'Open Discussion' });
			await expect(openDiscussionLink).toHaveAttribute('href', /\/forum\/post\?id=\d+$/);
		});
	});
});
