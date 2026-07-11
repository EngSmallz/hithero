import { apiFetch } from '$lib/api/client';
import { requireBackendRole } from '$lib/server/auth';
import { actionErrorMessage, cookieHeaders, formMessage } from '$lib/server/form-actions';
import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';

type ApiMessage = { detail?: string; message?: string };

export const load: PageServerLoad = async ({ fetch, request, url }) => {
	await requireBackendRole({ fetch, request, url }, ['teacher', 'admin']);
	return {};
};

async function updateProfileSection(
	event: Parameters<Actions[string]>[0],
	path: string,
	successFallback: string
) {
	await requireBackendRole(event, ['teacher', 'admin']);
	let message: string;

	try {
		const result = await apiFetch<ApiMessage>(path, {
			fetch: event.fetch,
			method: 'POST',
			body: await event.request.formData(),
			headers: cookieHeaders(event.request)
		});
		message = formMessage(result, successFallback);
	} catch (error) {
		return fail(400, {
			success: false,
			message: actionErrorMessage(error, 'Update failed. Please try again.')
		});
	}

	redirect(303, `/teacher?profile_update=${encodeURIComponent(message)}`);
}

export const actions: Actions = {
	updateName: (event) =>
		updateProfileSection(event, '/profile/update_teacher_name/', 'Name updated.'),
	updateSchool: (event) =>
		updateProfileSection(event, '/profile/update_teacher_school/', 'School information updated.'),
	updateInfo: (event) => updateProfileSection(event, '/profile/update_info/', 'Info updated.'),
	updateWishlist: (event) =>
		updateProfileSection(event, '/profile/update_wishlist/', 'Wishlist updated.'),
	updateUrlId: (event) =>
		updateProfileSection(event, '/profile/update_url_id/', 'URL ID updated successfully.')
};
