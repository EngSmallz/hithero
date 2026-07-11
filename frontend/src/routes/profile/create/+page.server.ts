import { apiFetch } from '$lib/api/client';
import { normalizeStringOptions } from '$lib/api/options';
import { requireBackendRole } from '$lib/server/auth';
import { actionErrorMessage, cookieHeaders, formMessage } from '$lib/server/form-actions';
import { fail } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';

type ApiMessage = { detail?: string; message?: string; role?: string };

export const load: PageServerLoad = async ({ fetch, request, url }) => {
	await requireBackendRole({ fetch, request, url }, ['teacher', 'admin']);

	try {
		const states = normalizeStringOptions(
			await apiFetch<unknown>('/api/get_states/', {
				fetch
			})
		);

		return {
			states,
			backendUnavailable: false
		};
	} catch (error) {
		console.error('Unable to load profile creation school states', error);

		return {
			states: [],
			backendUnavailable: true
		};
	}
};

export const actions: Actions = {
	default: async ({ fetch, request, url }) => {
		await requireBackendRole({ fetch, request, url }, ['teacher', 'admin']);

		const submitted = await request.formData();

		try {
			const result = await apiFetch<ApiMessage>('/profile/create_teacher_profile/', {
				fetch,
				method: 'POST',
				body: submitted,
				headers: cookieHeaders(request)
			});

			return {
				success: result.role === 'teacher' || result.role === 'admin',
				message: formMessage(result, 'Teacher created successfully')
			};
		} catch (error) {
			return fail(400, {
				success: false,
				message: actionErrorMessage(
					error,
					'An error occurred during profile creation. Please try again.'
				)
			});
		}
	}
};
