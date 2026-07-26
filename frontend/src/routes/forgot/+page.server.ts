import { serverApiFetch } from '$lib/server/api';
import { actionErrorMessage, formMessage } from '$lib/server/form-actions';
import { fail } from '@sveltejs/kit';
import type { Actions } from './$types';

type ApiMessage = { detail?: string; message?: string };

export const actions: Actions = {
	default: async ({ fetch, request }) => {
		const submitted = await request.formData();

		try {
			const result = await serverApiFetch<ApiMessage>(
				{ fetch, request },
				'/profile/forgot_password/',
				{
					method: 'POST',
					body: submitted
				}
			);

			return {
				success: true,
				message: formMessage(
					result,
					'If an account exists, a reset link will be sent to your email.'
				)
			};
		} catch (error) {
			return fail(400, {
				success: false,
				message: actionErrorMessage(error, 'A network error occurred. Please try again.')
			});
		}
	}
};
