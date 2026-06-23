import { error } from '@sveltejs/kit';
import { apiFetch, ApiError } from '$lib/api/client';
import { requireBackendRole } from '$lib/server/auth';
import type { PageServerLoad } from './$types';

export type ValidationUser = {
	name: string;
	email: string;
	state: string;
	district: string;
	school: string;
	phone_number: string;
	report: number;
	emailed: number;
};

type ValidationListResponse = {
	new_users: ValidationUser[];
	role: 'admin' | 'teacher';
};

export const load: PageServerLoad = async ({ fetch, request, url }) => {
	await requireBackendRole({ fetch, request, url }, ['teacher', 'admin']);

	try {
		return await apiFetch<ValidationListResponse>('/api/validation_list/', {
			fetch,
			headers: request.headers.get('cookie') ? { cookie: request.headers.get('cookie') ?? '' } : {}
		});
	} catch (listError) {
		if (listError instanceof ApiError && listError.status === 403) {
			error(403, 'You do not have access to this page');
		}

		console.error('Unable to load validation list', listError);
		error(503, 'Validation list is temporarily unavailable');
	}
};
