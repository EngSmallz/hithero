import assert from 'node:assert/strict';
import test from 'node:test';
import { forwardRequestHeaders } from './forward-headers.ts';

test('forwards cookie and CSRF provenance headers', () => {
	const request = new Request('https://www.helpteachers.net/profile/edit', {
		headers: {
			cookie: 'session=signed',
			origin: 'https://www.helpteachers.net',
			referer: 'https://www.helpteachers.net/profile/edit'
		}
	});

	const headers = forwardRequestHeaders(request, { accept: 'application/json' });

	assert.equal(headers.get('cookie'), 'session=signed');
	assert.equal(headers.get('origin'), 'https://www.helpteachers.net');
	assert.equal(headers.get('referer'), 'https://www.helpteachers.net/profile/edit');
	assert.equal(headers.get('accept'), 'application/json');
});

test('does not overwrite an explicit internal request header', () => {
	const request = new Request('https://www.helpteachers.net/login', {
		headers: { origin: 'https://www.helpteachers.net' }
	});

	const headers = forwardRequestHeaders(request, { origin: 'https://override.example' });

	assert.equal(headers.get('origin'), 'https://override.example');
});
