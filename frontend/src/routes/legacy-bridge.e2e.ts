import { expect, test } from '@playwright/test';

const legacyRoutes = ['/forgot', '/profile/create'];

test.describe('legacy route bridge', () => {
	for (const path of legacyRoutes) {
		test(`${path} redirects to backend origin`, async ({ request }) => {
			const response = await request.get(path, { maxRedirects: 0 });

			expect(response.status()).toBe(302);
			expect(response.headers().location).toBe(`http://localhost:8000${path}`);
		});
	}

	test('/teacher/[urlId] redirects to backend origin', async ({ request }) => {
		const response = await request.get('/teacher/alice-adams', { maxRedirects: 0 });

		expect(response.status()).toBe(302);
		expect(response.headers().location).toBe('http://localhost:8000/teacher/alice-adams');
	});
});
