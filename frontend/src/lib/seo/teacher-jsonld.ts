import type { TeacherProfile } from '$lib/api/types';

export type TeacherPersonJsonLd = {
	'@context': 'https://schema.org';
	'@type': 'Person';
	name: string;
	url: string;
	description?: string;
	worksFor?: {
		'@type': 'EducationalOrganization';
		name: string;
	};
	address?: {
		'@type': 'PostalAddress';
		addressLocality?: string;
		addressRegion?: string;
	};
};

export function buildTeacherPersonJsonLd(
	teacher: TeacherProfile,
	canonicalUrl: string
): TeacherPersonJsonLd | null {
	const name = teacher.name?.trim();
	if (!name) {
		return null;
	}

	const description = teacher.about_me?.trim();
	const school = teacher.school?.trim();
	const county = teacher.county?.trim();
	const state = teacher.state?.trim();
	const structuredData: TeacherPersonJsonLd = {
		'@context': 'https://schema.org',
		'@type': 'Person',
		name,
		url: canonicalUrl
	};

	if (description) {
		structuredData.description = description;
	}
	if (school) {
		structuredData.worksFor = {
			'@type': 'EducationalOrganization',
			name: school
		};
	}
	if (county || state) {
		structuredData.address = {
			'@type': 'PostalAddress',
			...(county ? { addressLocality: county } : {}),
			...(state ? { addressRegion: state } : {})
		};
	}

	return structuredData;
}

/** Prevent JSON-LD strings from closing the containing HTML script element. */
export function serializeJsonLd(value: unknown): string {
	return (JSON.stringify(value) ?? '')
		.replaceAll('<', '\\u003c')
		.replaceAll('>', '\\u003e')
		.replaceAll('&', '\\u0026')
		.replaceAll('\u2028', '\\u2028')
		.replaceAll('\u2029', '\\u2029');
}
