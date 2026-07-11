import { apiFetch } from '$lib/api/client';
import { normalizeStringOptions } from '$lib/api/options';
import { actionErrorMessage, formMessage } from '$lib/server/form-actions';
import { fail } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';

type ApiMessage = { detail?: string; message?: string };

export const load: PageServerLoad = async ({ fetch }) => {
	try {
		const states = normalizeStringOptions(
			await apiFetch<unknown>('/api/get_states/', {
				fetch
			})
		);

		return {
			states,
			backendUnavailable: false
		};
	} catch (error) {
		console.error('Unable to load registration school states', error);

		return {
			states: [],
			backendUnavailable: true
		};
	}
};

export const actions: Actions = {
	default: async ({ fetch, request }) => {
		const submitted = await request.formData();
		const password = String(submitted.get('password') ?? '');
		const confirmPassword = String(submitted.get('confirm_password') ?? '');
		const recaptchaResponse = String(submitted.get('recaptcha_response') ?? '').trim();

		if (password !== confirmPassword) {
			return fail(400, {
				success: false,
				message: 'Passwords do not match. Please ensure both password fields are identical.'
			});
		}

		if (submitted.get('termsCheckbox') !== 'on') {
			return fail(400, {
				success: false,
				message: 'You must agree to the Terms and Conditions to register.'
			});
		}

		if (!recaptchaResponse) {
			return fail(400, {
				success: false,
				message: 'Please enable JavaScript and complete the reCAPTCHA verification.'
			});
		}

		try {
			const result = await apiFetch<ApiMessage>('/profile/register/', {
				fetch,
				method: 'POST',
				body: submitted
			});

			return {
				success: true,
				message: formMessage(result, 'Registration successful. Please check your email.')
			};
		} catch (error) {
			return fail(400, {
				success: false,
				message: actionErrorMessage(error, 'Registration failed. Please try again.')
			});
		}
	}
};
