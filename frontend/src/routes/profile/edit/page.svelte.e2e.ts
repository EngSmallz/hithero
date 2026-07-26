import { expect, test, type Page } from '@playwright/test';
import { installAuthenticatedSession } from '$lib/test/session';

const teacherProfile = {
	state: 'Washington',
	county: 'King',
	district: 'Seattle Public Schools',
	school: 'Evergreen Elementary',
	name: 'Avery Adams',
	wishlist_url: 'https://example.com/wishlist',
	about_me: 'I build a classroom where students can practice curiosity every day.',
	image_data: null
};

async function installTeacherEditorStubs(
	page: Page,
	options: { verifiedSchool?: boolean } = {}
) {
	await installAuthenticatedSession(page.context());
	await page.route('**/api/profile/', async (route) => {
		await route.fulfill({
			contentType: 'application/json',
			body: JSON.stringify({
				user_role: 'teacher',
				user_id: 12,
				user_email: 'teacher@example.test',
				...(options.verifiedSchool
					? {
							profile_prefill: {
								state: teacherProfile.state,
								county: teacherProfile.county,
								district: teacherProfile.district,
								school: teacherProfile.school
							}
						}
					: {})
			})
		});
	});
	await page.route('**/profile/myinfo/', async (route) => {
		await route.fulfill({
			contentType: 'application/json',
			body: JSON.stringify({
				state: teacherProfile.state,
				county: teacherProfile.county,
				district: teacherProfile.district,
				school: teacherProfile.school,
				teacher: teacherProfile.name
			})
		});
	});
	await page.route('**/api/get_teacher_info/', async (route) => {
		await route.fulfill({
			contentType: 'application/json',
			body: JSON.stringify(teacherProfile)
		});
	});
	await page.route('**/api/teacher_url/', async (route) => {
		await route.fulfill({
			contentType: 'application/json',
			body: JSON.stringify({ url: 'www.HelpTeachers.net/teacher/avery-adams' })
		});
	});
	await page.route('**/api/get_states/', async (route) => {
		await route.fulfill({
			contentType: 'application/json',
			body: JSON.stringify(['Washington'])
		});
	});
	await page.route('**/api/get_counties/Washington', async (route) => {
		await route.fulfill({
			contentType: 'application/json',
			body: JSON.stringify(['King'])
		});
	});
	await page.route('**/api/get_districts/Washington/King', async (route) => {
		await route.fulfill({
			contentType: 'application/json',
			body: JSON.stringify(['Seattle Public Schools'])
		});
	});
	await page.route(
		'**/api/get_schools/Washington/King/Seattle%20Public%20Schools',
		async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify(['Evergreen Elementary', 'Roosevelt High School'])
			});
		}
	);
}

test.describe('/profile/edit', () => {
	test('renders prefilled teacher profile edit forms', async ({ page }) => {
		await installTeacherEditorStubs(page);

		await page.goto('/profile/edit', { waitUntil: 'domcontentloaded' });

		await expect(
			page.getByRole('heading', { level: 1, name: 'Edit Teacher Profile' })
		).toBeVisible();
		await expect(page.getByLabel(/^Name/)).toHaveValue('Avery Adams');
		await expect(page.getByRole('combobox', { name: /^State/ })).toHaveValue('Washington');
		await expect(page.getByRole('combobox', { name: /^County/ })).toHaveValue('King');
		await expect(page.getByRole('combobox', { name: /^School District/ })).toHaveValue(
			'Seattle Public Schools'
		);
		await expect(page.getByRole('combobox', { name: /^School required$/ })).toHaveValue(
			'Evergreen Elementary'
		);
		await expect(page.getByLabel(/^About Me/)).toHaveValue(teacherProfile.about_me);
		await expect(page.getByLabel(/^Amazon Wishlist URL/)).toHaveValue(
			'https://example.com/wishlist'
		);
		await expect(page.getByLabel(/^URL ID/)).toHaveValue('avery-adams');
		await expect(page.locator('meta[name="robots"]')).toHaveAttribute(
			'content',
			'noindex, nofollow'
		);
	});

	test('redirects unauthenticated visitors to login before rendering', async ({ page }) => {
		await page.goto('/profile/edit', { waitUntil: 'domcontentloaded' });

		await expect(page).toHaveURL('/login?redirect=%2Fprofile%2Fedit');
	});

	test('opens mobile navigation', async ({ page }) => {
		await installTeacherEditorStubs(page);
		await page.setViewportSize({ width: 390, height: 844 });

		await page.goto('/profile/edit', { waitUntil: 'domcontentloaded' });
		await page.getByRole('button', { name: 'Open navigation' }).click();

		const mobileNav = page.getByRole('navigation', { name: 'Mobile primary' });
		await expect(mobileNav).toBeVisible();
		await expect(mobileNav.getByRole('link', { name: 'Donate' })).toBeVisible();
		await expect(mobileNav.getByRole('button', { name: 'Logout' })).toBeVisible();
	});

	test('submits an about-me update and returns to the teacher page', async ({ page }) => {
		await installTeacherEditorStubs(page);
		await page.route('**/profile/update_info/', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify({ message: 'Info updated.' })
			});
		});
		await page.route('**/api/check_access_teacher/', async (route) => {
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify({ status: 'success' })
			});
		});

		await page.goto('/profile/edit', { waitUntil: 'domcontentloaded' });
		await page.getByLabel(/^About Me/).fill('Updated classroom story.');
		await page.getByRole('button', { name: 'Update About Me' }).click();

		await expect(page).toHaveURL('/teacher');
	});

	test('keeps verified school values read-only until an explicit confirmed change request', async ({
		page
	}) => {
		await installTeacherEditorStubs(page, { verifiedSchool: true });
		let requestBody = '';
		await page.route('**/profile/request_school_change/', async (route) => {
			requestBody = route.request().postData() || '';
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify({ message: 'School change submitted for reapproval.' })
			});
		});

		await page.goto('/profile/edit', { waitUntil: 'domcontentloaded' });
		await expect(page.getByRole('button', { name: 'Update School' })).toBeVisible();
		await expect(page.locator('#school')).toHaveAttribute('readonly', '');

		await page.getByRole('button', { name: 'Update School' }).click();
		await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible();
		await expect(page.getByRole('button', { name: 'Save Updated School' })).toBeVisible();
		await expect(page.getByRole('button', { name: 'Update School' })).toHaveCount(0);

		const school = page.getByRole('combobox', { name: /^School required$/ });
		await school.selectOption({ label: 'Roosevelt High School' });
		await page.getByRole('button', { name: 'Cancel' }).click();
		await expect(page.locator('#school')).toHaveValue('Evergreen Elementary');
		await expect(page.getByRole('button', { name: 'Update School' })).toBeVisible();

		await page.getByRole('button', { name: 'Update School' }).click();
		await school.selectOption({ label: 'Roosevelt High School' });
		page.once('dialog', async (dialog) => {
			expect(dialog.message()).toContain(
				'removed from public and search results until the new school is reapproved'
			);
			await dialog.accept();
		});
		await page.getByRole('button', { name: 'Save Updated School' }).click();

		await expect.poll(() => requestBody).toContain('Roosevelt High School');
		await expect(page).toHaveURL('/teacher');
	});

	test('opens wishlist setup help', async ({ page }) => {
		await installTeacherEditorStubs(page);

		await page.goto('/profile/edit', { waitUntil: 'domcontentloaded' });
		await expect(page.locator('[data-profile-enhanced]')).toHaveAttribute(
			'data-profile-enhanced',
			'true'
		);
		await page.getByRole('button', { name: 'How to Get Link' }).click();

		const dialog = page.getByRole('dialog', { name: 'Wishlist setup' });
		await expect(dialog).toBeVisible();
		await expect(dialog.locator('iframe')).toHaveAttribute('src', '/wishlist-setup');
	});
});
