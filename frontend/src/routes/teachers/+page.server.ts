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
	page: 1,
	page_size: 24,
	total_pages: 0,
	applied_filters: appliedFilters
});

const getOptionalSearchParam = (url: URL, key: string): string | undefined => {
	const value = url.searchParams.get(key)?.trim();
	return value || undefined;
};

const getPage = (url: URL): number => {
	const page = Number(url.searchParams.get('page'));
	return Number.isInteger(page) && page > 0 ? page : 1;
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
				page: getPage(url),
				page_size: 24
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
