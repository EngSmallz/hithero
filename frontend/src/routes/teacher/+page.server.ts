import { ApiError } from '$lib/api/client';
import type { TeacherProfile } from '$lib/api/types';
import { serverApiFetch } from '$lib/server/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch, request, parent }) => {
	const { profile } = await parent();
	if (!profile || !['teacher', 'admin'].includes(profile.user_role)) {
		return { teacher: null, currentTeacherState: 'session-selected' as const };
	}

	try {
		const teacher = await serverApiFetch<TeacherProfile>(
			{ fetch, request },
			'/api/current_teacher/'
		);
		return { teacher, currentTeacherState: 'ready' as const };
	} catch (loadError) {
		if (loadError instanceof ApiError && loadError.status === 404) {
			return { teacher: null, currentTeacherState: 'not-found' as const };
		}

		console.error('Unable to load current teacher profile', loadError);
		return { teacher: null, currentTeacherState: 'backend-unavailable' as const };
	}
};
