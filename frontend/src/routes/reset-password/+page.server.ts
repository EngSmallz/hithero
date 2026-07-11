import { apiFetch } from '$lib/api/client';
import { actionErrorMessage, formMessage } from '$lib/server/form-actions';
import { fail } from '@sveltejs/kit';
import type { Actions } from './$types';

type ApiMessage = { detail?: string; message?: string };

export const actions: Actions = {
	default: async ({ fetch, request }) => {
		const submitted = await request.formData();
		const newPassword = String(submitted.get('new_password') ?? '');
		const confirmPassword = String(submitted.get('confirm_password') ?? '');

		if (newPassword !== confirmPassword) {
			return fail(400, {
				success: false,
				message: 'Passwords do not match.'
			});
		}

		try {
			const result = await apiFetch<ApiMessage>('/profile/reset_password/', {
				fetch,
				method: 'POST',
				body: submitted
			});

			return {
				success: true,
				message: formMessage(result, 'Password reset successfully. You can now log in.')
			};
		} catch (error) {
			return fail(400, {
				success: false,
				message: actionErrorMessage(error, 'An error occurred. Please try again.')
			});
		}
	}
};
