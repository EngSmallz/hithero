import { apiFetch } from '$lib/api/client';
import { normalizeStringOptions } from '$lib/api/options';
import { requireBackendRole } from '$lib/server/auth';
import { serverApiFetch } from '$lib/server/api';
import { actionErrorMessage, formMessage } from '$lib/server/form-actions';
import { fail } from '@sveltejs/kit';
import type { BackendProfile, ProfilePrefill } from '$lib/api/types';
import type { Actions, PageServerLoad } from './$types';

type ApiMessage = { detail?: string; message?: string; role?: string };

export const load: PageServerLoad = async ({ fetch, request, url }) => {
	await requireBackendRole({ fetch, request, url }, ['teacher', 'admin']);
	let profilePrefill: ProfilePrefill | null = null;

	try {
		const profile = await serverApiFetch<BackendProfile>({ fetch, request }, '/api/profile/');
		profilePrefill = profile.profile_prefill ?? null;
	} catch (error) {
		console.error('Unable to load approved registration details', error);
	}

	try {
		const states = normalizeStringOptions(
			await apiFetch<unknown>('/api/get_states/', {
				fetch
			})
		);

		return {
			states,
			profilePrefill,
			backendUnavailable: false
		};
	} catch (error) {
		console.error('Unable to load profile creation school states', error);

		return {
			states: [],
			profilePrefill,
			backendUnavailable: true
		};
	}
};

export const actions: Actions = {
	default: async ({ fetch, request, url }) => {
		await requireBackendRole({ fetch, request, url }, ['teacher', 'admin']);

		const submitted = await request.formData();

		try {
			const result = await serverApiFetch<ApiMessage>(
				{ fetch, request },
				'/profile/create_teacher_profile/',
				{
					method: 'POST',
					body: submitted
				}
			);

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
