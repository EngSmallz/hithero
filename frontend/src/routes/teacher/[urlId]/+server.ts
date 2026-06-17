import { redirectToLegacy } from '$lib/server/legacyRedirect';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = ({ params }) => {
	return redirectToLegacy(`/teacher/${params.urlId}`);
};

export const HEAD = GET;
