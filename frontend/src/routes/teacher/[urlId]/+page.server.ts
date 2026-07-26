import { error } from '@sveltejs/kit';
import { apiFetch, ApiError } from '$lib/api/client';
import type { TeacherProfile } from '$lib/api/types';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, params }) => {
	try {
		const teacher = await apiFetch<TeacherProfile>(
			`/api/teacher/${encodeURIComponent(params.urlId)}/`,
			{ fetch }
		);

		return { teacher };
	} catch (loadError) {
		if (loadError instanceof ApiError && loadError.status === 404) {
			error(404, 'Teacher not found');
		}

		console.error('Unable to load public teacher profile', loadError);
		error(503, 'Teacher profile is temporarily unavailable');
	}
};
