const FORWARDED_REQUEST_HEADERS = ['cookie', 'origin', 'referer'] as const;

/** Copy trusted browser/session context into an internal SvelteKit API request. */
export function forwardRequestHeaders(request: Request, initial?: HeadersInit): Headers {
	const headers = new Headers(initial);
	for (const name of FORWARDED_REQUEST_HEADERS) {
		const value = request.headers.get(name);
		if (value && !headers.has(name)) {
			headers.set(name, value);
		}
	}
	return headers;
}
