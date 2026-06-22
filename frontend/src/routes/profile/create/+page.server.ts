import { apiFetch } from '$lib/api/client';
import { requireBackendRole } from '$lib/server/auth';
import type { PageServerLoad } from './$types';

const normalizeOptions = (value: unknown): string[] => {
	if (!Array.isArray(value)) {
		return [];
	}

	return value.filter((item): item is string => typeof item === 'string' && item.length > 0);
};

export const load: PageServerLoad = async ({ fetch, request, url }) => {
	await requireBackendRole({ fetch, request, url }, ['teacher', 'admin']);

	try {
		const states = normalizeOptions(
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
