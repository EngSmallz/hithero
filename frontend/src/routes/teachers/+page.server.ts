import { apiFetch } from '$lib/api/client';
import type { TeacherDirectoryResponse } from '$lib/api/types';
import type { PageServerLoad } from './$types';

const emptyDirectory = (
	appliedFilters: TeacherDirectoryResponse['applied_filters']
): TeacherDirectoryResponse => ({
	teachers: [],
	filters: {
		states: [],
		counties: [],
		districts: [],
		schools: []
	},
	total: 0,
	applied_filters: appliedFilters
});

const getOptionalSearchParam = (url: URL, key: string): string | undefined => {
	const value = url.searchParams.get(key)?.trim();
	return value || undefined;
};

export const load: PageServerLoad = async ({ fetch, url }) => {
	const selectedFilters = {
		state: getOptionalSearchParam(url, 'state'),
		county: getOptionalSearchParam(url, 'county'),
		district: getOptionalSearchParam(url, 'district'),
		school: getOptionalSearchParam(url, 'school')
	};

	try {
		const directory = await apiFetch<TeacherDirectoryResponse>('/api/teachers/', {
			fetch,
			query: {
				...selectedFilters,
				limit: 200
			}
		});

		return {
			directory,
			backendUnavailable: false
		};
	} catch (error) {
		console.error('Unable to load teacher directory', error);

		return {
			directory: emptyDirectory(selectedFilters),
			backendUnavailable: true
		};
	}
};
