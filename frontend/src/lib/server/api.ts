import { apiFetch, type ApiRequestOptions } from '$lib/api/client';
import { forwardRequestHeaders } from './forward-headers';

export type ServerApiEvent = {
	fetch: typeof fetch;
	request: Request;
};

/** Proxy a backend request from a SvelteKit server event with its cookie. */
export function serverApiFetch<T>(
	event: ServerApiEvent,
	path: string,
	options: ApiRequestOptions = {}
): Promise<T> {
	const headers = forwardRequestHeaders(event.request, options.headers);

	return apiFetch<T>(path, {
		...options,
		fetch: event.fetch,
		headers
	});
}
