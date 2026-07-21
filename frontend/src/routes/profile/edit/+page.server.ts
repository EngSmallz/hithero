import { requireBackendRole } from '$lib/server/auth';
import { serverApiFetch } from '$lib/server/api';
import { normalizeStringOptions } from '$lib/api/options';
import { actionErrorMessage, formMessage } from '$lib/server/form-actions';
import { error, fail, redirect } from '@sveltejs/kit';
import type { ProfilePrefill } from '$lib/api/types';
import type { Actions, PageServerLoad } from './$types';

type ApiMessage = { detail?: string; message?: string };
type MyInfoResponse = {
	state?: string;
	county?: string;
	district?: string;
	school?: string;
	teacher?: string;
	message?: string;
};
type TeacherProfile = {
	state?: string | null;
	county?: string | null;
	district?: string | null;
	school?: string | null;
	name?: string | null;
	wishlist_url?: string | null;
	about_me?: string | null;
	url_id?: string | null;
};

type BackendProfile = {
	profile_prefill?: ProfilePrefill | null;
};

const mergeOptions = (primary: string[], selected: string): string[] =>
	Array.from(new Set([selected, ...primary].filter(Boolean))).sort();

export const load: PageServerLoad = async ({ fetch, request, url }) => {
	await requireBackendRole({ fetch, request, url }, ['teacher', 'admin']);
	const event = { fetch, request };
	let myInfo: MyInfoResponse;

	try {
		myInfo = await serverApiFetch<MyInfoResponse>(event, '/profile/myinfo/');
	} catch (loadError) {
		console.error('Unable to load profile editor identity', loadError);
		error(503, 'Teacher profile information is temporarily unavailable');
	}

	let teacherInfo: TeacherProfile = {};
	try {
		teacherInfo = await serverApiFetch<TeacherProfile>(event, '/api/current_teacher/');
	} catch (loadError) {
		console.error('Unable to load optional teacher profile details', loadError);
	}

	let schoolVerified = false;
	try {
		const profile = await serverApiFetch<BackendProfile>(event, '/api/profile/');
		schoolVerified = Boolean(
			profile.profile_prefill?.state &&
			profile.profile_prefill?.county &&
			profile.profile_prefill?.district &&
			profile.profile_prefill?.school
		);
	} catch (loadError) {
		console.error('Unable to load profile verification status', loadError);
	}

	const state = teacherInfo.state || myInfo.state || '';
	const county = teacherInfo.county || myInfo.county || '';
	const district = teacherInfo.district || myInfo.district || '';
	const school = teacherInfo.school || myInfo.school || '';
	let schoolOptionsUnavailable = false;

	async function options(path: string, selected: string): Promise<string[]> {
		try {
			return mergeOptions(
				normalizeStringOptions(await serverApiFetch<unknown>(event, path)),
				selected
			);
		} catch (loadError) {
			console.error(`Unable to load profile editor options from ${path}`, loadError);
			schoolOptionsUnavailable = true;
			return mergeOptions([], selected);
		}
	}

	const states = await options('/api/get_states/', state);
	const counties = state
		? await options(`/api/get_counties/${encodeURIComponent(state)}`, county)
		: mergeOptions([], county);
	const districts =
		state && county
			? await options(
					`/api/get_districts/${encodeURIComponent(state)}/${encodeURIComponent(county)}`,
					district
				)
			: mergeOptions([], district);
	const schools =
		state && county && district
			? await options(
					`/api/get_schools/${encodeURIComponent(state)}/${encodeURIComponent(county)}/${encodeURIComponent(district)}`,
					school
				)
			: mergeOptions([], school);

	return {
		profile: {
			teacherName: teacherInfo.name || myInfo.teacher || '',
			aboutMe: teacherInfo.about_me || '',
			wishlist: teacherInfo.wishlist_url || '',
			urlId: teacherInfo.url_id || '',
			state,
			county,
			district,
			school
		},
		schoolOptions: { states, counties, districts, schools },
		schoolOptionsUnavailable,
		schoolVerified
	};
};

async function updateProfileSection(
	event: Parameters<Actions[string]>[0],
	path: string,
	successFallback: string
) {
	await requireBackendRole(event, ['teacher', 'admin']);
	let message: string;

	try {
		const result = await serverApiFetch<ApiMessage>(event, path, {
			method: 'POST',
			body: await event.request.formData()
		});
		message = formMessage(result, successFallback);
	} catch (error) {
		return fail(400, {
			success: false,
			message: actionErrorMessage(error, 'Update failed. Please try again.')
		});
	}

	redirect(303, `/teacher?profile_update=${encodeURIComponent(message)}`);
}

export const actions: Actions = {
	updateName: (event) =>
		updateProfileSection(event, '/profile/update_teacher_name/', 'Name updated.'),
	updateSchool: (event) =>
		updateProfileSection(event, '/profile/update_teacher_school/', 'School information updated.'),
	requestSchoolChange: (event) =>
		updateProfileSection(
			event,
			'/profile/request_school_change/',
			'School change submitted for reapproval.'
		),
	updateInfo: (event) => updateProfileSection(event, '/profile/update_info/', 'Info updated.'),
	updateWishlist: (event) =>
		updateProfileSection(event, '/profile/update_wishlist/', 'Wishlist updated.'),
	updateUrlId: (event) =>
		updateProfileSection(event, '/profile/update_url_id/', 'URL ID updated successfully.')
};
