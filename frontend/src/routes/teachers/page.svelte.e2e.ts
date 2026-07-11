import { execFileSync } from 'node:child_process';
import { expect, test, type Page } from '@playwright/test';

const state = 'P109';
const county = 'North';
const district = 'Paging District';
const school = 'Pagination School';

function seedTeacherDirectory() {
	const script = String.raw`
import os
from sqlalchemy import delete

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("TEST_DATABASE_URL", "sqlite:///./.tmp/hithero-playwright.sqlite")

import app

app.init_db()
db = app.SessionLocal()
try:
    db.execute(delete(app.TeacherList))
    teachers = []
    for index in range(1, 31):
        teachers.append(
            app.TeacherList(
                name=f"P109 Teacher {index:02d}",
                state="P109",
                county="North",
                district="Paging District",
                school="Pagination School",
                regUserID=9000 + index,
                wishlist_url=f"https://example.test/p109-{index:02d}",
                about_me="Pagination coverage teacher",
                url_id=f"p109-teacher-{index:02d}",
            )
        )
    db.add_all(teachers)
    db.commit()
finally:
    db.close()
`;

	execFileSync(process.env.PYTHON ?? 'python3', ['-c', script], {
		cwd: '..',
		env: {
			...process.env,
			APP_ENV: 'test',
			SECRET_KEY: 'test-secret',
			TEST_DATABASE_URL:
				process.env.TEST_DATABASE_URL ?? 'sqlite:///./.tmp/hithero-playwright.sqlite',
			PYTHONPATH: 'tests/stubs'
		}
	});
}

function teacherCards(page: Page) {
	return page.locator('a[href^="/teacher/p109-teacher-"]');
}

test.describe('/teachers pagination', () => {
	test.describe.configure({ mode: 'serial' });

	test.beforeEach(() => {
		seedTeacherDirectory();
	});

	test('/teachers?page=2 renders the expected page and page label', async ({ page }) => {
		await page.goto('/teachers?page=2', { waitUntil: 'domcontentloaded' });

		await expect(page.getByText('30 teachers found')).toBeVisible();
		await expect(page.getByText('Page 2 of 2')).toBeVisible();
		await expect(teacherCards(page)).toHaveCount(6);
		await expect(page.getByRole('link', { name: /P109 Teacher 25/ })).toBeVisible();
		await expect(page.getByRole('link', { name: /P109 Teacher 30/ })).toBeVisible();
		await expect(page.getByRole('link', { name: 'Previous' })).toHaveAttribute(
			'href',
			'/teachers?page=1'
		);
		await expect(page.getByRole('link', { name: 'Next' })).toHaveCount(0);
	});

	test('previous and next pagination links preserve selected filters', async ({ page }) => {
		await page.goto(
			`/teachers?state=${state}&county=${county}&district=${encodeURIComponent(
				district
			)}&school=${encodeURIComponent(school)}`,
			{ waitUntil: 'domcontentloaded' }
		);

		await expect(page.getByText('Page 1 of 2')).toBeVisible();
		await expect(teacherCards(page)).toHaveCount(24);

		const nextHref = `/teachers?state=${state}&county=${county}&district=${encodeURIComponent(
			district
		)}&school=${encodeURIComponent(school)}&page=2`;
		await expect(page.getByRole('link', { name: 'Next' })).toHaveAttribute('href', nextHref);

		await page.getByRole('link', { name: 'Next' }).click();
		await expect(page).toHaveURL(nextHref);
		await expect(page.getByText('Page 2 of 2')).toBeVisible();

		const previousHref = `/teachers?state=${state}&county=${county}&district=${encodeURIComponent(
			district
		)}&school=${encodeURIComponent(school)}&page=1`;
		await expect(page.getByRole('link', { name: 'Previous' })).toHaveAttribute(
			'href',
			previousHref
		);
	});

	test('out-of-range page requests clamp to the last available page', async ({ page }) => {
		await page.goto('/teachers?state=P109&page=99', { waitUntil: 'domcontentloaded' });

		await expect(page.getByText('Page 2 of 2')).toBeVisible();
		await expect(teacherCards(page)).toHaveCount(6);
		await expect(page.getByRole('link', { name: 'Next' })).toHaveCount(0);
	});

	test('empty results remain clear and expose a clean clear-filters link', async ({ page }) => {
		await page.goto('/teachers?state=NoMatches', { waitUntil: 'domcontentloaded' });

		await expect(page.getByText('0 teachers found')).toBeVisible();
		await expect(page.getByText('No teachers found for your selection')).toBeVisible();
		await expect(page.getByRole('link', { name: 'Clear Filters' })).toHaveAttribute(
			'href',
			'/teachers'
		);
		await expect(page.getByText(/Page \d+ of \d+/)).toHaveCount(0);
	});
});
