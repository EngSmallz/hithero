export const site = {
	name: 'Homeroom Heroes',
	origin: 'https://www.helpteachers.net',
	defaultDescription:
		'Homeroom Heroes connects educators with community supporters who help fund classroom supplies.',
	defaultOgImage: '/images/logo_transparent.png'
} as const;

export const routes = {
	home: '/',
	teachers: '/teachers',
	register: '/register',
	about: '/about',
	contact: '/contact',
	partners: '/partners',
	terms: '/terms',
	wishlistSetup: '/wishlist-setup',
	login: '/login',
	forgot: '/forgot',
	resetPassword: '/reset-password',
	forum: '/forum',
	forumNew: '/forum/new',
	forumPost: '/forum/post',
	teacher: '/teacher',
	updatePassword: '/update-password',
	profileCreate: '/profile/create',
	profileEdit: '/profile/edit',
	validation: '/validation',
	admin: '/admin',
	forbidden: '/403',
	notFound: '/404'
} as const;

export type RouteHref = (typeof routes)[keyof typeof routes];

export type NavItem = {
	label: string;
	href: RouteHref;
};

export const publicNavItems: NavItem[] = [
	{ label: 'Home', href: routes.home },
	{ label: 'Donate', href: routes.teachers },
	{ label: 'Sign Up', href: routes.register },
	{ label: 'About', href: routes.about },
	{ label: 'Contact', href: routes.contact },
	{ label: 'Partners', href: routes.partners }
];

export function isExternalHref(href: string): boolean {
	return /^(https?:)?\/\//.test(href) || href.startsWith('mailto:') || href.startsWith('tel:');
}

export function getCanonicalUrl(path = routes.home): string {
	if (/^https?:\/\//.test(path)) {
		return path;
	}

	const normalizedPath = path.startsWith('/') ? path : `/${path}`;
	return new URL(normalizedPath, site.origin).toString();
}
