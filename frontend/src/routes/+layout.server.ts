import { getBackendProfile } from '$lib/server/auth';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ fetch, request }) => ({
	profile: await getBackendProfile(fetch, request)
});
