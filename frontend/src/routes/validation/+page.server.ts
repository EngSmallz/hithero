import { error } from '@sveltejs/kit';
import { ApiError } from '$lib/api/client';
import { requireBackendRole } from '$lib/server/auth';
import { serverApiFetch } from '$lib/server/api';
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

export type SchoolChange = {
	id: number;
	user_id: number;
	old: {
		state: string;
		county: string;
		district: string;
		school: string;
	};
	proposed: {
		state: string;
		county: string;
		district: string;
		school: string;
	};
	status: string;
	created_at: string | null;
};

type ValidationListResponse = {
	new_users: ValidationUser[];
	school_changes: SchoolChange[];
	role: 'admin' | 'teacher';
};

export const load: PageServerLoad = async ({ fetch, request, url }) => {
	await requireBackendRole({ fetch, request, url }, ['teacher', 'admin']);

	try {
		return await serverApiFetch<ValidationListResponse>(
			{ fetch, request },
			'/api/validation_list/'
		);
	} catch (listError) {
		if (listError instanceof ApiError && listError.status === 403) {
			error(403, 'You do not have access to this page');
		}

		console.error('Unable to load validation list', listError);
		error(503, 'Validation list is temporarily unavailable');
	}
};
