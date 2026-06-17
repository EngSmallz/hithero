import { env } from '$env/dynamic/public';
import type { ApiErrorBody } from './types';

const DEFAULT_BACKEND_ORIGIN = 'http://localhost:8000';

type QueryValue = string | number | boolean | null | undefined;

export type ApiRequestOptions = RequestInit & {
	backendOrigin?: string;
	fetch?: typeof fetch;
	query?: Record<string, QueryValue>;
};

export class ApiError extends Error {
	status: number;
	body: ApiErrorBody | string | null;
	url: string;

	constructor(message: string, status: number, url: string, body: ApiErrorBody | string | null) {
		super(message);
		this.name = 'ApiError';
		this.status = status;
		this.url = url;
		this.body = body;
	}
}

export function getBackendOrigin(): string {
	return env.PUBLIC_BACKEND_ORIGIN || DEFAULT_BACKEND_ORIGIN;
}

export function buildApiUrl(
	path: string,
	query?: Record<string, QueryValue>,
	backendOrigin = getBackendOrigin()
): string {
	const url = new URL(path.startsWith('/') ? path : `/${path}`, backendOrigin);

	for (const [key, value] of Object.entries(query ?? {})) {
		if (value !== undefined && value !== null) {
			url.searchParams.set(key, String(value));
		}
	}

	return url.toString();
}

export async function apiFetch<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
	const { backendOrigin, fetch: customFetch, query, headers, ...init } = options;
	const requestUrl = buildApiUrl(path, query, backendOrigin);
	const fetcher = customFetch ?? fetch;

	const response = await fetcher(requestUrl, {
		credentials: 'include',
		headers: {
			accept: 'application/json',
			...headers
		},
		...init
	});

	if (!response.ok) {
		const body = await readErrorBody(response);
		const detail = typeof body === 'object' && body?.detail ? body.detail : response.statusText;
		throw new ApiError(detail, response.status, requestUrl, body);
	}

	if (response.status === 204) {
		return undefined as T;
	}

	return (await response.json()) as T;
}

async function readErrorBody(response: Response): Promise<ApiErrorBody | string | null> {
	const contentType = response.headers.get('content-type') ?? '';

	if (contentType.includes('application/json')) {
		return (await response.json()) as ApiErrorBody;
	}

	const text = await response.text();
	return text || null;
}
