import { buildApiUrl } from '$lib/api/client';
import { formMessage } from '$lib/server/form-actions';
import { fail, redirect } from '@sveltejs/kit';
import type { Cookies } from '@sveltejs/kit';
import type { Actions } from './$types';

type LoginResponse = {
	message?: string;
	createCount?: number;
	role?: string;
};

function getSafeRedirect(value: string | null, origin: string): string | null {
	if (!value?.startsWith('/')) {
		return null;
	}

	try {
		const destination = new URL(value, origin);
		return destination.origin === origin
			? `${destination.pathname}${destination.search}${destination.hash}`
			: null;
	} catch {
		return null;
	}
}

function copySessionCookie(response: Response, cookies: Cookies, secure: boolean) {
	const setCookie =
		typeof response.headers.getSetCookie === 'function'
			? response.headers.getSetCookie()[0]
			: response.headers.get('set-cookie');

	if (!setCookie) {
		return;
	}

	const match = setCookie.match(/^session=([^;]+)/);
	if (!match) {
		return;
	}

	cookies.set('session', decodeURIComponent(match[1]), {
		path: '/',
		httpOnly: true,
		sameSite: 'lax',
		secure
	});
}

export const actions: Actions = {
	default: async ({ cookies, fetch, request, url }) => {
		const submitted = await request.formData();
		const response = await fetch(buildApiUrl('/profile/login/'), {
			method: 'POST',
			body: submitted,
			credentials: 'include',
			headers: {
				accept: 'application/json',
				...(request.headers.get('origin') ? { origin: request.headers.get('origin') ?? '' } : {}),
				...(request.headers.get('referer') ? { referer: request.headers.get('referer') ?? '' } : {})
			}
		});
		const body = (await response.json().catch(() => ({}))) as LoginResponse;
		const message = formMessage(body, 'Login failed. Please check your credentials and try again.');

		if (!response.ok || !body.role) {
			return fail(response.ok ? 400 : response.status, {
				success: false,
				message
			});
		}

		copySessionCookie(response, cookies, url.protocol === 'https:');

		if (body.role === 'teacher' && body.createCount === 0) {
			redirect(303, '/profile/create');
		}

		redirect(303, getSafeRedirect(url.searchParams.get('redirect'), url.origin) || '/');
	}
};
