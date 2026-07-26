import assert from 'node:assert/strict';
import test from 'node:test';
import { buildTeacherPersonJsonLd, serializeJsonLd } from './teacher-jsonld.ts';

test('builds a public Person JSON-LD object from visible teacher fields', () => {
	const teacher = {
		name: '  Avery Adams  ',
		url_id: 'avery-adams',
		state: 'Washington',
		county: 'King',
		district: 'Seattle Public Schools',
		school: 'Evergreen Elementary',
		about_me: 'I support curious classrooms.',
		wishlist_url: 'https://private.example/wishlist',
		image_data: 'private-image-data'
	};

	assert.deepEqual(
		buildTeacherPersonJsonLd(teacher, 'https://www.helpteachers.net/teacher/avery-adams'),
		{
			'@context': 'https://schema.org',
			'@type': 'Person',
			name: 'Avery Adams',
			url: 'https://www.helpteachers.net/teacher/avery-adams',
			description: 'I support curious classrooms.',
			worksFor: {
				'@type': 'EducationalOrganization',
				name: 'Evergreen Elementary'
			},
			address: {
				'@type': 'PostalAddress',
				addressLocality: 'King',
				addressRegion: 'Washington'
			}
		}
	);
});

test('serializes hostile public text without creating HTML', () => {
	const structuredData = buildTeacherPersonJsonLd(
		{
			name: '</script><script>alert(1)</script>',
			url_id: 'safe-id',
			about_me: 'A & B',
			state: 'State',
			county: 'County'
		},
		'https://www.helpteachers.net/teacher/safe-id'
	);
	const serialized = serializeJsonLd(structuredData);

	assert.equal(serialized.includes('</script>'), false);
	assert.deepEqual(JSON.parse(serialized), structuredData);
});
