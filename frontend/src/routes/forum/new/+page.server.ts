import { requireBackendRole } from '$lib/server/auth';
import { ApiError } from '$lib/api/client';
import { serverApiFetch } from '$lib/server/api';
import { fail } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';

type CreatedPost = {
	id?: number;
	title?: string;
	content?: string;
	detail?: string;
	message?: string;
};

export const load: PageServerLoad = async ({ fetch, request, url }) => {
	await requireBackendRole({ fetch, request, url }, ['teacher', 'admin', 'user']);
	return {};
};

export const actions: Actions = {
	default: async ({ fetch, request, url }) => {
		await requireBackendRole({ fetch, request, url }, ['teacher', 'admin', 'user']);

		const submitted = await request.formData();
		const title = String(submitted.get('title') ?? '').trim();
		const content = String(submitted.get('content') ?? '').trim();

		if (!title || !content) {
			return fail(400, {
				success: false,
				message: 'Please add both a title and content before creating the discussion.',
				title,
				content
			});
		}

		const formData = new FormData();
		formData.set('title', title);
		formData.set('content', content);

		try {
			const createdPost = await serverApiFetch<CreatedPost>(
				{ fetch, request },
				'/forum/create_post',
				{
					method: 'POST',
					body: formData
				}
			);

			if (!createdPost.id) {
				return fail(502, {
					success: false,
					message:
						createdPost.detail ||
						createdPost.message ||
						'The discussion was submitted, but the new post could not be opened automatically.',
					title,
					content
				});
			}

			return {
				success: true,
				message: 'Discussion created.',
				postId: createdPost.id,
				title: createdPost.title || title,
				content: createdPost.content || content
			};
		} catch (error) {
			const message =
				error instanceof ApiError
					? error.message
					: 'An error occurred while creating the discussion.';

			return fail(502, {
				success: false,
				message,
				title,
				content
			});
		}
	}
};
