import { redirectToLegacy } from '$lib/server/legacyRedirect';

export function GET() {
	return redirectToLegacy('/forgot');
}
