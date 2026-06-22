import { redirectToLegacy } from '$lib/server/legacyRedirect';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = () => redirectToLegacy('/admin');
export const HEAD = GET;
