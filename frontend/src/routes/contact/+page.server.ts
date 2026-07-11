import { apiFetch } from '$lib/api/client';
import { actionErrorMessage, formMessage } from '$lib/server/form-actions';
import { fail } from '@sveltejs/kit';
import type { Actions } from './$types';

type ApiMessage = { detail?: string; message?: string };

export const actions: Actions = {
	default: async ({ fetch, request }) => {
		const submitted = await request.formData();
		const recaptchaResponse = String(submitted.get('recaptcha_response') ?? '').trim();

		if (!recaptchaResponse) {
			return fail(400, {
				success: false,
				message: 'Please enable JavaScript and complete the reCAPTCHA to send your message.'
			});
		}

		try {
			const result = await apiFetch<ApiMessage>('/api/contact_us/', {
				fetch,
				method: 'POST',
				body: submitted
			});

			return {
				success: true,
				message: formMessage(result, 'Message sent successfully.')
			};
		} catch (error) {
			return fail(400, {
				success: false,
				message: actionErrorMessage(error, 'An error occurred. Please try again.')
			});
		}
	}
};
