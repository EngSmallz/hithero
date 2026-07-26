const WISHLIST_AFFILIATE_TAG = 'h0mer00mher0-20';

export function normalizeWishlistInput(value: string | null | undefined): string {
	const raw = value?.trim();
	if (!raw) {
		return '';
	}

	const candidate = /^https?:\/\//i.test(raw) ? raw : `https://${raw.replace(/^\/+/, '')}`;
	try {
		const url = new URL(candidate);
		url.search = '';
		return url.toString();
	} catch {
		return candidate;
	}
}

export function buildWishlistUrl(value: string | null | undefined): string {
	const normalized = normalizeWishlistInput(value);
	if (!normalized) {
		return '';
	}

	try {
		const url = new URL(normalized);
		url.searchParams.set('tag', WISHLIST_AFFILIATE_TAG);
		return url.toString();
	} catch {
		return normalized;
	}
}
