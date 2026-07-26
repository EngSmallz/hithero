import { execFileSync } from 'node:child_process';
import type { BrowserContext } from '@playwright/test';
import type { UserRole } from '$lib/api/types';

export async function installAuthenticatedSession(
	context: BrowserContext,
	role: UserRole = 'teacher'
) {
	const python = process.env.PYTHON ?? 'python3';
	const payload = JSON.stringify({
		user_id: 12,
		user_role: role,
		user_email: `${role}@example.test`
	});
	const script = [
		'import sys',
		'from base64 import b64encode',
		'from itsdangerous import TimestampSigner',
		'print(TimestampSigner("test-secret").sign(b64encode(sys.argv[1].encode())).decode())'
	].join(';');
	const value = execFileSync(python, ['-c', script, payload], { encoding: 'utf8' }).trim();

	await context.addCookies([
		{
			name: 'session',
			value,
			url: 'http://localhost:4173',
			httpOnly: true,
			sameSite: 'Lax'
		}
	]);
}
