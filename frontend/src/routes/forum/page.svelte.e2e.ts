import { expect, test, type Page } from '@playwright/test';
import { installAuthenticatedSession } from '$lib/test/session';

const forumPosts = [
	{
		id: 101,
		title: '<strong>Newest</strong> discussion',
		content: 'This discussion was rendered from a <em>mocked forum API response</em>.',
		created_at: '2026-06-10T12:00:00',
		user_id: 7,
		upvote_count: 3,
		comment_count: 1
	},
	{
		id: 102,
		title: 'Older highly voted discussion',
		content: 'A discussion with more upvotes for sorting coverage.',
		created_at: '2026-05-10T12:00:00',
		user_id: 8,
		upvote_count: 12,
		comment_count: 0
	},
	{
		id: 103,
		title: 'Oldest discussion',
		content: 'The oldest classroom discussion in this mocked list.',
		created_at: '2026-04-10T12:00:00',
		user_id: 9,
		upvote_count: 1,
		comment_count: 4
	}
];

async function installForumPostsStub(page: Page, posts = forumPosts) {
	await page.route('**/forum/get_posts', async (route) => {
		await route.fulfill({
			contentType: 'application/json',
			body: JSON.stringify(posts)
		});
	});
}

function postCards(page: Page) {
	return page.locator('#posts-container a');
}

test.describe('/forum', () => {
	test.beforeEach(async ({ context }) => {
		await installAuthenticatedSession(context);
	});

	test('redirects unauthenticated visitors to login before rendering', async ({
		page,
		context
	}) => {
		await context.clearCookies();
		await page.goto('/forum');

		await expect(page).toHaveURL('/login?redirect=%2Fforum');
	});

	test('renders forum posts in initial server HTML', async ({ page }) => {
		await installForumPostsStub(page);

		const response = await page.goto('/forum', { waitUntil: 'domcontentloaded' });
		expect(await response?.text()).toContain('Newest');
		expect(await response?.text()).toContain('mocked forum API response');

		await expect(
			page.getByRole('heading', { level: 1, name: "The Teachers' Lounge" })
		).toBeVisible();
		await expect(page.getByRole('link', { name: /Newest discussion/ })).toHaveAttribute(
			'href',
			'/forum/post?id=101'
		);
		await expect(page.getByText('mocked forum API response')).toBeVisible();
		await expect(page.locator('#posts-container strong')).toHaveText('Newest');
		await expect(page.getByRole('link', { name: '+ New Post' })).toHaveAttribute(
			'href',
			'/forum/new'
		);
		await expect(page.locator('meta[name="robots"]')).toHaveAttribute(
			'content',
			'noindex, nofollow'
		);
	});

	test('sorts posts by upvotes and oldest date', async ({ page }) => {
		await installForumPostsStub(page);

		await page.goto('/forum', { waitUntil: 'domcontentloaded' });

		await page.getByRole('button', { name: 'Upvotes' }).click();
		await expect(postCards(page).first()).toContainText('Older highly voted discussion');

		await page.getByRole('button', { name: 'Date (Oldest)' }).click();
		await expect(postCards(page).first()).toContainText('Oldest discussion');
	});

	test('filters posts by search term and clears search', async ({ page }) => {
		await installForumPostsStub(page);

		await page.goto('/forum', { waitUntil: 'domcontentloaded' });
		await page.getByLabel('Search posts by keyword').fill('highly voted');

		await expect(postCards(page)).toHaveCount(1);
		await expect(postCards(page).first()).toContainText('Older highly voted discussion');

		await page.getByRole('button', { name: 'Clear' }).click();

		expect(await postCards(page).count()).toBeGreaterThanOrEqual(3);
	});

	test('shows no-results messaging for unmatched search', async ({ page }) => {
		await installForumPostsStub(page);

		await page.goto('/forum', { waitUntil: 'domcontentloaded' });
		await page.getByLabel('Search posts by keyword').fill('not in this list');

		await expect(page.getByText('No discussions found matching your search')).toBeVisible();
	});

	test('loads discussions beyond the initial ten', async ({ page }) => {
		const response = await page.goto('/forum', { waitUntil: 'domcontentloaded' });
		expect(await response?.text()).toContain('Additional discussion 9');

		await expect(postCards(page)).toHaveCount(10);
		await expect(page.locator('[data-forum-enhanced]')).toHaveAttribute(
			'data-forum-enhanced',
			'true'
		);
		await page.getByRole('button', { name: 'Load 10 More Discussions' }).click();
		await expect(page.locator('#posts-container a[href="/forum/post?id=104"]')).toBeVisible();
		expect(await postCards(page).count()).toBeGreaterThan(10);
	});

	test('opens mobile navigation', async ({ page }) => {
		await installForumPostsStub(page);
		await page.setViewportSize({ width: 390, height: 844 });

		await page.goto('/forum', { waitUntil: 'domcontentloaded' });
		await page.getByRole('button', { name: 'Open navigation' }).click();

		const mobileNav = page.getByRole('navigation', { name: 'Mobile primary' });
		await expect(mobileNav).toBeVisible();
		await expect(mobileNav.getByRole('link', { name: 'Donate' })).toBeVisible();
		await expect(mobileNav.getByRole('link', { name: 'My Page' })).toBeVisible();
		await expect(mobileNav.getByRole('button', { name: 'Logout' })).toBeVisible();
	});
});
