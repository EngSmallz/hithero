import { env } from '$env/dynamic/public';
import { redirect } from '@sveltejs/kit';

const DEFAULT_BACKEND_ORIGIN = 'http://localhost:8000';

export function redirectToLegacy(path: string): never {
	const backendOrigin = env.PUBLIC_BACKEND_ORIGIN || DEFAULT_BACKEND_ORIGIN;
	throw redirect(302, new URL(path, backendOrigin).toString());
}
