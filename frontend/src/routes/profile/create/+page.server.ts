import { apiFetch } from '$lib/api/client';
import { normalizeStringOptions } from '$lib/api/options';
import { requireBackendRole } from '$lib/server/auth';
import type { PageServerLoad } from './$types';

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
