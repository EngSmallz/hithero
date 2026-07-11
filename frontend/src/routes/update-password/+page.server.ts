import { apiFetch } from '$lib/api/client';
import { actionErrorMessage, cookieHeaders, formMessage } from '$lib/server/form-actions';
import { requireBackendRole } from '$lib/server/auth';
import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';

type ApiMessage = { detail?: string; message?: string; status?: string };

export const load: PageServerLoad = async ({ fetch, request, url }) => {
	await requireBackendRole({ fetch, request, url }, ['teacher', 'admin', 'user']);
	return {};
};

export const actions: Actions = {
	default: async ({ fetch, request, url }) => {
		await requireBackendRole({ fetch, request, url }, ['teacher', 'admin', 'user']);

		const submitted = await request.formData();
		let message = 'Password update did not complete. Please try again.';
		let shouldRedirect = false;

		try {
			const result = await apiFetch<ApiMessage>('/profile/update_password/', {
				fetch,
				method: 'POST',
				body: submitted,
				headers: cookieHeaders(request)
			});
			message = formMessage(result, message);

			if (result.status === 'success' || result.message === 'Password updated successfully') {
				shouldRedirect = true;
			}
		} catch (error) {
			return fail(400, {
				success: false,
				message: actionErrorMessage(error, 'An error occurred. Please try again.')
			});
		}

		if (shouldRedirect) {
			redirect(303, '/teacher');
		}

		return fail(400, {
			success: false,
			message
		});
	}
};
