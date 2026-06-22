import { error, redirect } from '@sveltejs/kit';
import { apiFetch, ApiError } from '$lib/api/client';
import type { BackendProfile, UserRole } from '$lib/api/types';

type AuthEvent = {
	fetch: typeof fetch;
	request: Request;
	url: URL;
};

function requestHeaders(request: Request): HeadersInit | undefined {
	const cookie = request.headers.get('cookie');
	return cookie ? { cookie } : undefined;
}

export async function getBackendProfile(
	fetcher: typeof fetch,
	request: Request
): Promise<BackendProfile | null> {
	try {
		return await apiFetch<BackendProfile>('/api/profile/', {
			fetch: fetcher,
			headers: requestHeaders(request)
		});
	} catch (profileError) {
		if (profileError instanceof ApiError && [401, 404].includes(profileError.status)) {
			return null;
		}

		console.error('Unable to load the authenticated profile', profileError);
		return null;
	}
}

export async function requireBackendRole(
	event: AuthEvent,
	allowedRoles: UserRole[]
): Promise<BackendProfile> {
	let profile: BackendProfile;

	try {
		profile = await apiFetch<BackendProfile>('/api/profile/', {
			fetch: event.fetch,
			headers: requestHeaders(event.request)
		});
	} catch (profileError) {
		if (profileError instanceof ApiError && [401, 404].includes(profileError.status)) {
			const returnTo = `${event.url.pathname}${event.url.search}`;
			redirect(303, `/login?redirect=${encodeURIComponent(returnTo)}`);
		}

		console.error('Unable to verify the authenticated profile', profileError);
		error(503, 'Account access is temporarily unavailable');
	}

	if (!allowedRoles.includes(profile.user_role)) {
		error(403, 'You do not have access to this page');
	}

	return profile;
}
