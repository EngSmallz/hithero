import { expect, test, type Page } from '@playwright/test';

const forumPosts = [
	{
		id: 101,
		title: 'Newest discussion',
		content: 'This discussion was rendered from a mocked forum API response.',
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
	test('renders mocked backend forum posts', async ({ page }) => {
		await installForumPostsStub(page);

		await page.goto('/forum', { waitUntil: 'domcontentloaded' });

		await expect(
			page.getByRole('heading', { level: 1, name: "The Teachers' Lounge" })
		).toBeVisible();
		await expect(page.getByRole('link', { name: /Newest discussion/ })).toHaveAttribute(
			'href',
			'/forum/post?id=101'
		);
		await expect(page.getByText('mocked forum API response')).toBeVisible();
		await expect(page.getByRole('link', { name: '+ New Post' })).toHaveAttribute(
			'href',
			'/forum/new'
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

		await expect(postCards(page)).toHaveCount(3);
	});

	test('shows no-results messaging for unmatched search', async ({ page }) => {
		await installForumPostsStub(page);

		await page.goto('/forum', { waitUntil: 'domcontentloaded' });
		await page.getByLabel('Search posts by keyword').fill('not in this list');

		await expect(page.getByText('No discussions found matching your search')).toBeVisible();
	});

	test('loads more than the initial ten posts', async ({ page }) => {
		await installForumPostsStub(
			page,
			Array.from({ length: 12 }, (_, index) => ({
				id: 200 + index,
				title: `Discussion ${index + 1}`,
				content: `Post ${index + 1}`,
				created_at: `2026-06-${String(index + 1).padStart(2, '0')}T12:00:00`,
				user_id: 7,
				upvote_count: index,
				comment_count: 0
			}))
		);

		await page.goto('/forum', { waitUntil: 'domcontentloaded' });

		await expect(postCards(page)).toHaveCount(10);
		await page.getByRole('button', { name: 'Load 10 More Discussions' }).click();
		await expect(postCards(page)).toHaveCount(12);
	});

	test('opens mobile navigation', async ({ page }) => {
		await installForumPostsStub(page);
		await page.setViewportSize({ width: 390, height: 844 });

		await page.goto('/forum', { waitUntil: 'domcontentloaded' });
		await page.getByRole('button', { name: 'Open navigation' }).click();

		const mobileNav = page.getByRole('navigation', { name: 'Mobile primary' });
		await expect(mobileNav).toBeVisible();
		await expect(mobileNav.getByRole('link', { name: 'Donate' })).toBeVisible();
		await expect(mobileNav.getByRole('link', { name: 'Login' })).toBeVisible();
	});

	test('shows backend errors without hiding the page', async ({ page }) => {
		await page.route('**/forum/get_posts', async (route) => {
			await route.fulfill({
				status: 500,
				contentType: 'application/json',
				body: JSON.stringify({ detail: 'Could not retrieve posts due to a server error.' })
			});
		});

		await page.goto('/forum', { waitUntil: 'domcontentloaded' });

		await expect(page.getByRole('alert')).toContainText('Could not retrieve posts');
		await expect(
			page.getByRole('heading', { level: 1, name: "The Teachers' Lounge" })
		).toBeVisible();
	});
});
