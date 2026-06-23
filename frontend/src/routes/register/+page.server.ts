import { apiFetch } from '$lib/api/client';
import { normalizeStringOptions } from '$lib/api/options';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
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
		console.error('Unable to load registration school states', error);

		return {
			states: [],
			backendUnavailable: true
		};
	}
};
