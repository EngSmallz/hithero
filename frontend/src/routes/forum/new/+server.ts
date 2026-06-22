import { redirectToLegacy } from '$lib/server/legacyRedirect';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = () => {
	return redirectToLegacy('/forum/new');
};

export const HEAD = GET;
