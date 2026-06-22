import { redirectToLegacy } from '$lib/server/legacyRedirect';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = () => redirectToLegacy('/validation');
export const HEAD = GET;
