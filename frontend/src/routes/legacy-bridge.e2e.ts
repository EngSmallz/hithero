import { expect, test } from '@playwright/test';

test.describe('legacy route bridge', () => {
	test('/forum/new redirects to backend origin', async ({ request }) => {
		const response = await request.get('/forum/new', { maxRedirects: 0 });

		expect(response.status()).toBe(302);
		expect(response.headers().location).toBe('http://localhost:8001/forum/new');
	});
});
