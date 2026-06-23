import { expect, test } from '@playwright/test';

test.describe('legacy route bridge', () => {
	for (const [path, location] of [
		['/admin', 'http://localhost:8001/admin'],
		['/validation', 'http://localhost:8001/validation']
	]) {
		test(`${path} redirects to backend origin`, async ({ request }) => {
			const response = await request.get(path, { maxRedirects: 0 });

			expect(response.status()).toBe(302);
			expect(response.headers().location).toBe(location);
		});
	}
});
