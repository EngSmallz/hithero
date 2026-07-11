import { ApiError } from '$lib/api/client';

export function cookieHeaders(request: Request): HeadersInit | undefined {
	const cookie = request.headers.get('cookie');
	return cookie ? { cookie } : undefined;
}

export function actionErrorMessage(error: unknown, fallback: string): string {
	return error instanceof ApiError ? error.message : fallback;
}

export function formMessage(body: unknown, fallback: string): string {
	if (body && typeof body === 'object') {
		const value = body as { detail?: unknown; message?: unknown };
		if (typeof value.detail === 'string') {
			return value.detail;
		}
		if (typeof value.message === 'string') {
			return value.message;
		}
	}

	return fallback;
}
