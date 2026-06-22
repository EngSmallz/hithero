<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import Alert from '$lib/components/Alert.svelte';
	import Button from '$lib/components/Button.svelte';
	import FormField from '$lib/components/FormField.svelte';
	import PageShell from '$lib/components/PageShell.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { getBackendOrigin } from '$lib/api/client';
	import type { BackendProfile } from '$lib/api/types';
	import { routes } from '$lib/routes';
	import type { PageData } from './$types';

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

	type ApiMessage = { detail?: string; message?: string };
	type StatusVariant = 'info' | 'success' | 'warning' | 'error';
	type StatusMessage = { variant: StatusVariant; message: string };

	let { data } = $props<{ data: PageData }>();

	const backendOrigin = getBackendOrigin();
	const postId = page.url.searchParams.get('id')?.trim() || '';
	const inputClass =
		'block min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-950 shadow-sm focus:border-green-600 focus:outline-2 focus:outline-green-600';

	let profile = $derived<BackendProfile | null>(data.profile);
	let post = $state<ForumPost | null>(null);
	let comments = $state<ForumComment[]>([]);
	let status = $state<StatusMessage | null>({
		variant: 'info',
		message: 'Loading post details...'
	});
	let commentsStatus = $state<StatusMessage | null>(null);
	let actionStatus = $state<StatusMessage | null>(null);
	let isBusy = $state(false);
	let isEditingPost = $state(false);
	let editTitle = $state('');
	let editContent = $state('');
	let newComment = $state('');
	let editingCommentId = $state<number | null>(null);
	let editingCommentContent = $state('');

	let isAuthenticated = $derived(profile !== null);
	let currentUserId = $derived(profile ? Number(profile.user_id) : null);
	let canEditPost = $derived(Boolean(post && currentUserId === post.user_id));
	let canDeletePost = $derived(Boolean(post && profile?.user_role === 'admin'));
	let title = $derived(
		post?.title ? `${post.title} - Homeroom Heroes` : 'Homeroom Heroes - Discussion Detail'
	);
	let description = $derived(
		post?.content
			? `Read a Homeroom Heroes forum discussion: ${post.content.substring(0, 140)}`
			: 'Read a Homeroom Heroes forum discussion.'
	);
	let canonicalPath = $derived(
		postId ? `${routes.forumPost}?id=${encodeURIComponent(postId)}` : routes.forumPost
	);

	onMount(() => {
		void loadPostDetail();
	});

	async function loadPostDetail() {
		if (!postId) {
			status = {
				variant: 'error',
				message:
					'Post ID is missing from the URL. Please ensure you are navigating from the forum list.'
			};
			return;
		}

		status = { variant: 'info', message: 'Loading post details...' };
		try {
			post = await fetchJson<ForumPost>(
				`${backendOrigin}/forum/get_post?post_id=${encodeURIComponent(postId)}`
			);
			editTitle = post.title;
			editContent = post.content;
			status = null;
			await loadComments(post.id);
		} catch (error) {
			status = {
				variant: 'error',
				message:
					error instanceof Error
						? `Failed to load post ${postId}: ${error.message}`
						: 'Network Error: Could not reach the server to fetch the post.'
			};
		}
	}

	async function loadComments(id: number) {
		commentsStatus = { variant: 'info', message: 'Loading comments...' };
		try {
			comments = await fetchJson<ForumComment[]>(`${backendOrigin}/forum/comments/${id}/`);
			commentsStatus = null;
		} catch (error) {
			comments = [];
			commentsStatus = {
				variant: 'error',
				message:
					error instanceof Error
						? `Failed to load comments: ${error.message}`
						: 'Network error. Could not load comments.'
			};
		}
	}

	async function vote(voteType: 1 | -1) {
		if (!post) return;
		await runAction(async () => {
			post = await fetchJson<ForumPost>(`${backendOrigin}/forum/posts/${post?.id}/vote`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ vote_type: voteType })
			});
		}, 'Your vote was recorded.');
	}

	async function savePostEdit(event: SubmitEvent) {
		event.preventDefault();
		if (!post) return;
		await runAction(async () => {
			post = await fetchJson<ForumPost>(`${backendOrigin}/forum/post/${post?.id}/update`, {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ title: editTitle, content: editContent })
			});
			isEditingPost = false;
		}, 'Discussion updated.');
	}

	async function deletePost() {
		if (!post || !window.confirm('Delete this discussion permanently?')) return;
		await runAction(async () => {
			await fetchJson<void>(`${backendOrigin}/forum/post/${post?.id}/delete`, {
				method: 'DELETE'
			});
			await goto(resolve(routes.forum));
		}, 'Discussion deleted.');
	}

	async function addComment(event: SubmitEvent) {
		event.preventDefault();
		const activePost = post;
		if (!activePost || !newComment.trim()) return;
		await runAction(async () => {
			const formData = new FormData();
			formData.set('content', newComment.trim());
			const createdComment = await fetchJson<ForumComment>(
				`${backendOrigin}/forum/posts/${activePost.id}/comment`,
				{ method: 'POST', body: formData }
			);
			comments = [createdComment, ...comments];
			post = { ...activePost, comment_count: (activePost.comment_count || 0) + 1 };
			newComment = '';
		}, 'Comment posted.');
	}

	function beginCommentEdit(comment: ForumComment) {
		editingCommentId = comment.id;
		editingCommentContent = comment.content;
		actionStatus = null;
	}

	async function saveCommentEdit(event: SubmitEvent, commentId: number) {
		event.preventDefault();
		const formData = new FormData();
		formData.set('content', editingCommentContent.trim());
		await runAction(async () => {
			const updated = await fetchJson<ForumComment>(
				`${backendOrigin}/forum/comment/${commentId}/update`,
				{ method: 'PATCH', body: formData }
			);
			comments = comments.map((comment) => (comment.id === commentId ? updated : comment));
			editingCommentId = null;
			editingCommentContent = '';
		}, 'Comment updated.');
	}

	async function deleteComment(commentId: number) {
		const activePost = post;
		if (!activePost || !window.confirm('Delete this comment permanently?')) return;
		await runAction(async () => {
			await fetchJson<ApiMessage>(`${backendOrigin}/forum/comment/${commentId}/delete`, {
				method: 'DELETE'
			});
			comments = comments.filter((comment) => comment.id !== commentId);
			post = {
				...activePost,
				comment_count: Math.max(0, (activePost.comment_count || 0) - 1)
			};
		}, 'Comment deleted.');
	}

	async function runAction(action: () => Promise<void>, successMessage: string) {
		isBusy = true;
		actionStatus = null;
		try {
			await action();
			actionStatus = { variant: 'success', message: successMessage };
		} catch (error) {
			actionStatus = {
				variant: 'error',
				message: error instanceof Error ? error.message : 'The action could not be completed.'
			};
		} finally {
			isBusy = false;
		}
	}

	async function fetchJson<T>(url: string, init: RequestInit = {}): Promise<T> {
		const response = await fetch(url, { ...init, credentials: 'include' });
		if (!response.ok) {
			const body = (await response.json().catch(() => ({}))) as ApiMessage;
			throw new Error(body.detail || body.message || response.statusText || 'Request failed.');
		}
		if (response.status === 204) return undefined as T;
		return (await response.json()) as T;
	}

	function canManageComment(comment: ForumComment): boolean {
		return profile?.user_role === 'admin' || currentUserId === comment.user_id;
	}

	function formatDate(value: string): string {
		const date = new Date(value);
		if (Number.isNaN(date.getTime())) return value;
		return date.toLocaleDateString(undefined, {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}
</script>

<Seo {title} {description} path={canonicalPath} noindex />

<PageShell eyebrow="Forum" title="Discussion Detail" narrow={false}>
	<div class="mx-auto max-w-4xl space-y-6">
		<Button href={routes.forum} variant="secondary">Back to Forum</Button>

		{#if status}<Alert variant={status.variant}>{status.message}</Alert>{/if}
		{#if actionStatus}<Alert variant={actionStatus.variant}>{actionStatus.message}</Alert>{/if}

		{#if post}
			<article class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
				{#if isEditingPost}
					<form class="space-y-5" onsubmit={savePostEdit}>
						<FormField id="edit-post-title" label="Discussion title" required>
							<input id="edit-post-title" class={inputClass} required bind:value={editTitle} />
						</FormField>
						<FormField id="edit-post-content" label="Discussion content" required>
							<textarea
								id="edit-post-content"
								class={`${inputClass} min-h-40 resize-y`}
								required
								bind:value={editContent}></textarea>
						</FormField>
						<div class="flex flex-wrap gap-3">
							<Button type="submit" disabled={isBusy}>Save Discussion</Button>
							<Button type="button" variant="secondary" onclick={() => (isEditingPost = false)}>
								Cancel
							</Button>
						</div>
					</form>
				{:else}
					<div class="border-b border-slate-200 pb-5">
						<div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
							<div class="flex items-center gap-2 text-sm font-semibold text-slate-700">
								<span class="rounded-full bg-slate-100 px-3 py-1"
									>{post.upvote_count || 0} upvotes</span
								>
								<span class="rounded-full bg-slate-100 px-3 py-1"
									>{post.comment_count || 0} comments</span
								>
							</div>
							<p class="text-sm text-slate-500">
								Posted by <span class="font-semibold text-slate-700">{post.user_id}</span> on
								{formatDate(post.created_at)}
							</p>
						</div>
					</div>

					<div class="pt-6">
						<h2 class="text-4xl font-extrabold tracking-normal text-green-800">{post.title}</h2>
						<p class="mt-6 whitespace-pre-wrap text-lg leading-8 text-slate-700">{post.content}</p>
					</div>

					{#if isAuthenticated}
						<div class="mt-6 flex flex-wrap gap-3 border-t border-slate-200 pt-5">
							<Button type="button" size="sm" disabled={isBusy} onclick={() => void vote(1)}
								>Upvote</Button
							>
							<Button
								type="button"
								size="sm"
								variant="secondary"
								disabled={isBusy}
								onclick={() => void vote(-1)}
							>
								Downvote
							</Button>
							{#if canEditPost}
								<Button
									type="button"
									size="sm"
									variant="secondary"
									onclick={() => (isEditingPost = true)}
								>
									Edit Discussion
								</Button>
							{/if}
							{#if canDeletePost}
								<Button
									type="button"
									size="sm"
									variant="secondary"
									disabled={isBusy}
									onclick={() => void deletePost()}
								>
									Delete Discussion
								</Button>
							{/if}
						</div>
					{/if}
				{/if}
			</article>

			<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
				<h2 class="text-2xl font-bold tracking-normal text-green-800">
					{post.comment_count || comments.length} Comments
				</h2>

				{#if isAuthenticated}
					<form class="mt-5 space-y-4" onsubmit={addComment}>
						<FormField id="new-comment" label="Add a comment" required>
							<textarea
								id="new-comment"
								class={`${inputClass} min-h-28 resize-y`}
								required
								bind:value={newComment}></textarea>
						</FormField>
						<Button type="submit" disabled={isBusy || !newComment.trim()}>Post Comment</Button>
					</form>
				{:else}
					<Alert variant="info">
						<a class="font-semibold underline" href={resolve(routes.login)}>Log in</a> to vote or join
						the discussion.
					</Alert>
				{/if}

				{#if commentsStatus}
					<div class="mt-5">
						<Alert variant={commentsStatus.variant}>{commentsStatus.message}</Alert>
					</div>
				{/if}

				{#if !commentsStatus && comments.length === 0}
					<p class="mt-5 rounded-md bg-slate-50 p-4 text-slate-600">
						No comments yet. Be the first to start the discussion!
					</p>
				{:else if comments.length > 0}
					<div class="mt-5 space-y-4">
						{#each comments as comment (comment.id)}
							<article class="rounded-lg border-l-4 border-green-600 bg-slate-50 p-4">
								{#if editingCommentId === comment.id}
									<form class="space-y-3" onsubmit={(event) => saveCommentEdit(event, comment.id)}>
										<label
											class="block text-sm font-semibold text-slate-800"
											for={`comment-${comment.id}-edit`}
										>
											Edit comment
										</label>
										<textarea
											id={`comment-${comment.id}-edit`}
											class={`${inputClass} min-h-24 resize-y`}
											required
											bind:value={editingCommentContent}></textarea>
										<div class="flex gap-2">
											<Button type="submit" size="sm" disabled={isBusy}>Save Comment</Button>
											<Button
												type="button"
												size="sm"
												variant="secondary"
												onclick={() => (editingCommentId = null)}
											>
												Cancel
											</Button>
										</div>
									</form>
								{:else}
									<p class="whitespace-pre-wrap text-sm leading-6 text-slate-700">
										{comment.content}
									</p>
									<p class="mt-3 text-xs text-slate-500">
										Comment by User ID: <span class="font-semibold text-slate-700"
											>{comment.user_id}</span
										>
										on {formatDate(comment.created_at)}
									</p>
									{#if canManageComment(comment)}
										<div class="mt-3 flex gap-2">
											{#if currentUserId === comment.user_id}
												<Button
													type="button"
													size="sm"
													variant="secondary"
													onclick={() => beginCommentEdit(comment)}
												>
													Edit Comment
												</Button>
											{/if}
											<Button
												type="button"
												size="sm"
												variant="secondary"
												disabled={isBusy}
												onclick={() => void deleteComment(comment.id)}
											>
												Delete Comment
											</Button>
										</div>
									{/if}
								{/if}
							</article>
						{/each}
					</div>
				{/if}
			</section>
		{/if}
	</div>
</PageShell>
