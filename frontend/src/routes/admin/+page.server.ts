import { apiFetch } from '$lib/api/client';
import { normalizeStringOptions } from '$lib/api/options';
import { requireBackendRole } from '$lib/server/auth';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, request, url }) => {
	await requireBackendRole({ fetch, request, url }, ['admin']);

	try {
		const states = normalizeStringOptions(
			await apiFetch<unknown>('/api/index_states/', {
				fetch
			})
		);

		return {
			states,
			backendUnavailable: false
		};
	} catch (error) {
		console.error('Unable to load admin school states', error);

		return {
			states: [],
			backendUnavailable: true
		};
	}
};
