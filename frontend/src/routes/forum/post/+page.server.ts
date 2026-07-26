import { requireBackendRole } from '$lib/server/auth';
import { ApiError } from '$lib/api/client';
import { serverApiFetch } from '$lib/server/api';
import type { PageServerLoad } from './$types';

type ForumPost = {
	id: number;
	title: string;
	content: string;
	user_id: number;
	created_at: string;
	upvote_count?: number | null;
	comment_count?: number | null;
};

type ForumComment = {
	id: number;
	content: string;
	post_id: number;
	user_id: number;
	parent_comment_id?: number | null;
	created_at: string;
};

export const load: PageServerLoad = async ({ fetch, request, url }) => {
	await requireBackendRole({ fetch, request, url }, ['teacher', 'admin', 'user']);
	const postId = url.searchParams.get('id')?.trim();
	if (!postId || !/^\d+$/.test(postId)) {
		return { post: null, comments: [], detailState: 'invalid-id' as const };
	}

	try {
		const post = await serverApiFetch<ForumPost>({ fetch, request }, '/forum/get_post', {
			query: { post_id: postId }
		});
		try {
			const comments = await serverApiFetch<ForumComment[]>(
				{ fetch, request },
				`/forum/comments/${post.id}/`
			);
			return { post, comments, detailState: 'ready' as const };
		} catch (commentsError) {
			console.error('Unable to load forum comments', commentsError);
			return { post, comments: [], detailState: 'comments-unavailable' as const };
		}
	} catch (loadError) {
		if (loadError instanceof ApiError && loadError.status === 404) {
			return { post: null, comments: [], detailState: 'not-found' as const };
		}
		console.error('Unable to load forum post', loadError);
		return { post: null, comments: [], detailState: 'backend-unavailable' as const };
	}
};
