import { expect, test, type Page } from '@playwright/test';
import { installAuthenticatedSession } from '$lib/test/session';

const forumPost = {
	id: 101,
	title: 'Detailed forum discussion',
	content: 'This discussion detail was rendered from a mocked forum API response.',
	created_at: '2026-06-10T12:00:00',
	user_id: 7,
	upvote_count: 3,
	comment_count: 2
};

const forumComments = [
	{
		id: 201,
		post_id: 101,
		user_id: 8,
		content: 'This comment was loaded from the comments endpoint.',
		parent_comment_id: null,
		created_at: '2026-06-11T12:00:00'
	},
	{
		id: 202,
		post_id: 101,
		user_id: 9,
		content: 'A second read-only comment.',
		parent_comment_id: null,
		created_at: '2026-06-12T12:00:00'
	}
];

async function installPostDetailStubs(page: Page) {
	await page.route('**/forum/get_post?post_id=101', async (route) => {
		await route.fulfill({
			contentType: 'application/json',
			body: JSON.stringify(forumPost)
		});
	});
	await page.route('**/forum/comments/101/', async (route) => {
		await route.fulfill({
			contentType: 'application/json',
			body: JSON.stringify(forumComments)
		});
	});
}

test.describe('/forum/post', () => {
	test('renders mocked backend post detail and comments', async ({ page }) => {
		await installPostDetailStubs(page);

		await page.goto('/forum/post?id=101', { waitUntil: 'domcontentloaded' });

		await expect(page.getByRole('heading', { level: 1, name: 'Discussion Detail' })).toBeVisible();
		await expect(
			page.getByRole('heading', { level: 2, name: 'Detailed forum discussion' })
		).toBeVisible();
		await expect(page.getByText('mocked forum API response')).toBeVisible();
		await expect(page.getByText('3 upvotes')).toBeVisible();
		await expect(page.getByText('2 comments', { exact: true })).toBeVisible();
		await expect(
			page.getByText('This comment was loaded from the comments endpoint.')
		).toBeVisible();
		await expect(page.getByText('A second read-only comment.')).toBeVisible();
		await expect(page.getByRole('link', { name: 'Back to Forum' })).toHaveAttribute(
			'href',
			'/forum'
		);
		await expect(page.getByRole('link', { name: 'Log in' })).toBeVisible();
		await expect(page.getByRole('button', { name: /Post Comment|Upvote|Downvote/ })).toHaveCount(0);
	});

	test('lets authenticated users vote and post comments', async ({ page }) => {
		await installAuthenticatedSession(page.context());
		await installPostDetailStubs(page);
		await page.route('**/forum/posts/101/vote', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify({ ...forumPost, upvote_count: 4 })
			});
		});
		await page.route('**/forum/posts/101/comment', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify({
					id: 203,
					post_id: 101,
					user_id: 12,
					content: 'A newly posted classroom comment.',
					parent_comment_id: null,
					created_at: '2026-06-13T12:00:00'
				})
			});
		});

		await page.goto('/forum/post?id=101', { waitUntil: 'domcontentloaded' });
		await page.getByRole('button', { name: 'Upvote' }).click();
		await expect(page.getByText('4 upvotes')).toBeVisible();

		await page.getByLabel('Add a comment').fill('A newly posted classroom comment.');
		await page.getByRole('button', { name: 'Post Comment' }).click();
		await expect(page.getByText('A newly posted classroom comment.')).toBeVisible();
		await expect(page.getByRole('status')).toContainText('Comment posted');
	});

	test('shows an error when the post id is missing', async ({ page }) => {
		await page.goto('/forum/post', { waitUntil: 'domcontentloaded' });

		await expect(page.getByRole('alert')).toContainText('Post ID is missing');
	});

	test('shows backend post loading errors', async ({ page }) => {
		await page.route('**/forum/get_post?post_id=404', async (route) => {
			await route.fulfill({
				status: 404,
				contentType: 'application/json',
				body: JSON.stringify({ detail: 'Post with ID 404 not found.' })
			});
		});

		await page.goto('/forum/post?id=404', { waitUntil: 'domcontentloaded' });

		await expect(page.getByRole('alert')).toContainText('Post with ID 404 not found');
	});

	test('keeps the post visible when comments fail to load', async ({ page }) => {
		await page.route('**/forum/get_post?post_id=101', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify(forumPost)
			});
		});
		await page.route('**/forum/comments/101/', async (route) => {
			await route.fulfill({
				status: 500,
				contentType: 'application/json',
				body: JSON.stringify({ detail: 'Could not retrieve comments due to a server error.' })
			});
		});

		await page.goto('/forum/post?id=101', { waitUntil: 'domcontentloaded' });

		await expect(
			page.getByRole('heading', { level: 2, name: 'Detailed forum discussion' })
		).toBeVisible();
		await expect(page.getByRole('alert')).toContainText('Could not retrieve comments');
	});

	test('opens mobile navigation', async ({ page }) => {
		await installPostDetailStubs(page);
		await page.setViewportSize({ width: 390, height: 844 });

		await page.goto('/forum/post?id=101', { waitUntil: 'domcontentloaded' });
		await page.getByRole('button', { name: 'Open navigation' }).click();

		const mobileNav = page.getByRole('navigation', { name: 'Mobile primary' });
		await expect(mobileNav).toBeVisible();
		await expect(mobileNav.getByRole('link', { name: 'Donate' })).toBeVisible();
		await expect(mobileNav.getByRole('link', { name: 'Login' })).toBeVisible();
	});
});
