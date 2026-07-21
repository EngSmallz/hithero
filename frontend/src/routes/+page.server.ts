import { serverApiFetch, type ServerApiEvent } from '$lib/server/api';
import type { PageServerLoad } from './$types';

type FeaturedTeacher = {
	name?: string | null;
	state?: string | null;
	county?: string | null;
	school?: string | null;
	image_data?: string | null;
	url_id?: string | null;
};

type Promo = {
	promo_image_url?: string | null;
	promo_title?: string | null;
};

async function optionalLoad<T>(
	event: ServerApiEvent,
	path: string,
	label: string
): Promise<{ value: T | null; unavailable: boolean }> {
	try {
		return { value: await serverApiFetch<T>(event, path), unavailable: false };
	} catch (error) {
		console.error(`Unable to load homepage ${label}`, error);
		return { value: null, unavailable: true };
	}
}

export const load: PageServerLoad = async ({ fetch, request }) => {
	const event = { fetch, request };
	const [spotlight, promo, randomTeacher] = await Promise.all([
		optionalLoad<FeaturedTeacher>(event, '/spotlight/teacher', 'spotlight'),
		optionalLoad<Promo>(event, '/promo/get_promo_info/', 'promotion'),
		optionalLoad<FeaturedTeacher>(event, '/api/random_teacher/', 'random teacher')
	]);
	const spotlightTeacher = spotlight.value ?? randomTeacher.value;

	return {
		spotlight: spotlightTeacher,
		promo: promo.value?.promo_image_url ? promo.value : null,
		randomTeacher: randomTeacher.value,
		spotlightUnavailable: spotlight.unavailable && !spotlightTeacher,
		promoUnavailable: promo.unavailable,
		randomTeacherUnavailable: randomTeacher.unavailable
	};
};
