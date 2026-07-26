import { requireBackendRole } from '$lib/server/auth';
import { serverApiFetch } from '$lib/server/api';
import type { PageServerLoad } from './$types';

export type ForumPost = {
	id: number;
	title: string;
	content: string;
	user_id: number;
	created_at: string;
	upvote_count?: number | null;
	comment_count?: number | null;
};

export const load: PageServerLoad = async ({ fetch, request, url }) => {
	await requireBackendRole({ fetch, request, url }, ['teacher', 'admin', 'user']);
	try {
		return {
			posts: await serverApiFetch<ForumPost[]>({ fetch, request }, '/forum/get_posts'),
			forumState: 'ready' as const
		};
	} catch (loadError) {
		console.error('Unable to load forum discussions', loadError);
		return { posts: [], forumState: 'backend-unavailable' as const };
	}
};
