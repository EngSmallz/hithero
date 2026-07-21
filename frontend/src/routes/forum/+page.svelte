<script lang="ts">
	/* eslint-disable svelte/no-at-html-tags */
	import { onMount, untrack } from 'svelte';
	import { resolve } from '$app/paths';
	import Alert from '$lib/components/Alert.svelte';
	import Button from '$lib/components/Button.svelte';
	import PageShell from '$lib/components/PageShell.svelte';
	import Seo from '$lib/components/Seo.svelte';
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
	type SortMode = 'date-newest' | 'date-oldest' | 'upvotes';
	type StatusVariant = 'info' | 'success' | 'warning' | 'error';
	type StatusMessage = { variant: StatusVariant; message: string };

	const sortOptions: { value: SortMode; label: string }[] = [
		{ value: 'date-newest', label: 'Date (Newest)' },
		{ value: 'date-oldest', label: 'Date (Oldest)' },
		{ value: 'upvotes', label: 'Upvotes' }
	];

	let { data } = $props<{ data: PageData }>();
	const initialData = untrack(() => data);
	let posts = $state<ForumPost[]>(initialData.posts);
	let searchTerm = $state('');
	let currentSort = $state<SortMode>('date-newest');
	let visibleCount = $state(10);
	let isEnhanced = $state(false);
	let status = $state<StatusMessage | null>(
		initialData.forumState === 'backend-unavailable'
			? { variant: 'error', message: 'The forum is temporarily unavailable.' }
			: null
	);

	let filteredPosts = $derived.by(() => {
		const normalizedSearch = searchTerm.trim().toLowerCase();
		const matchingPosts = normalizedSearch
			? posts.filter((post) => {
					const title = textContent(post.title).toLowerCase();
					const content = textContent(post.content).toLowerCase();
					return title.includes(normalizedSearch) || content.includes(normalizedSearch);
				})
			: posts;

		return sortPosts(matchingPosts, currentSort);
	});
	let visiblePosts = $derived(
		filteredPosts.slice(0, searchTerm ? filteredPosts.length : visibleCount)
	);
	let hasNoInitialPosts = $derived(posts.length === 0 && !status && !searchTerm.trim());
	let hasNoSearchResults = $derived(
		posts.length > 0 && searchTerm.trim() && filteredPosts.length === 0
	);
	let canLoadMore = $derived(!searchTerm.trim() && filteredPosts.length > visibleCount);

	onMount(() => {
		isEnhanced = true;
	});

	function setSort(value: SortMode) {
		currentSort = value;
	}

	function clearSearchFilter() {
		searchTerm = '';
		visibleCount = 10;
	}

	function loadMorePosts() {
		visibleCount += 10;
	}

	function sortPosts(items: ForumPost[], sortBy: SortMode): ForumPost[] {
		const sortedPosts = [...items];

		if (sortBy === 'upvotes') {
			return sortedPosts.sort((a, b) => {
				const voteDelta = (b.upvote_count || 0) - (a.upvote_count || 0);
				if (voteDelta !== 0) {
					return voteDelta;
				}
				return dateValue(b.created_at) - dateValue(a.created_at);
			});
		}

		if (sortBy === 'date-oldest') {
			return sortedPosts.sort((a, b) => dateValue(a.created_at) - dateValue(b.created_at));
		}

		return sortedPosts.sort((a, b) => dateValue(b.created_at) - dateValue(a.created_at));
	}

	function dateValue(value: string): number {
		const timestamp = new Date(value).getTime();
		return Number.isNaN(timestamp) ? 0 : timestamp;
	}

	function formatDate(value: string): string {
		const date = new Date(value);
		if (Number.isNaN(date.getTime())) {
			return value;
		}

		return date.toLocaleDateString(undefined, {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function excerpt(value: string): string {
		const plainText = textContent(value);
		return plainText.length > 200 ? `${plainText.substring(0, 200)}...` : plainText;
	}

	function textContent(value?: string | null): string {
		if (!value) {
			return '';
		}
		if (typeof document === 'undefined') {
			return value.replace(/<[^>]*>/g, ' ');
		}
		const container = document.createElement('div');
		container.innerHTML = value;
		return container.textContent || '';
	}
</script>

<Seo
	title="Homeroom Heroes - Forum Discussions"
	description="Browse teacher forum discussions in the Homeroom Heroes Teachers' Lounge."
	path={routes.forum}
	noindex
/>

<PageShell eyebrow="Forum" title="The Teachers' Lounge" narrow={false}>
	<div class="mx-auto max-w-4xl space-y-6" data-forum-enhanced={isEnhanced}>
		<div class="grid gap-3 sm:grid-cols-[1fr_auto]">
			<label class="sr-only" for="post-search-input">Search posts by keyword</label>
			<input
				id="post-search-input"
				type="text"
				placeholder="Search posts by keyword..."
				class="block min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-950 shadow-sm focus:border-green-600 focus:outline-2 focus:outline-green-600"
				bind:value={searchTerm}
			/>
			<Button type="button" variant="secondary" onclick={clearSearchFilter}>Clear</Button>
		</div>

		<section
			aria-label="Forum sorting"
			class="flex flex-col gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between"
		>
			<p class="text-base font-semibold text-green-800">Sort By:</p>
			<div class="flex flex-wrap gap-2">
				{#each sortOptions as option (option.value)}
					<Button
						type="button"
						variant={currentSort === option.value ? 'primary' : 'secondary'}
						size="sm"
						onclick={() => setSort(option.value)}
					>
						{option.label}
					</Button>
				{/each}
				<Button href={routes.forumNew} size="sm">+ New Post</Button>
			</div>
		</section>

		{#if status}
			<Alert variant={status.variant}>{status.message}</Alert>
		{/if}

		<section id="posts-container" aria-label="Forum posts" class="space-y-5">
			{#each visiblePosts as post (post.id)}
				<a
					href={resolve(`${routes.forumPost}?id=${encodeURIComponent(post.id)}` as '/')}
					class="block rounded-lg border border-slate-200 bg-white p-6 text-slate-950 shadow-sm transition hover:border-green-300 hover:bg-green-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-700"
				>
					<div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
						<h2 class="text-2xl font-bold tracking-normal text-green-800">
							{@html post.title}
						</h2>
						<div class="flex gap-2 text-xs font-semibold text-slate-700">
							<span class="rounded-full bg-slate-100 px-2 py-1">
								{post.upvote_count || 0}
								upvotes
							</span>
							<span class="rounded-full bg-slate-100 px-2 py-1">
								{post.comment_count || 0}
								comments
							</span>
						</div>
					</div>
					<p class="mt-3 border-b border-slate-200 pb-3 text-sm text-slate-500">
						Posted by User:
						<span class="font-medium text-slate-700">{post.user_id}</span>
						on {formatDate(post.created_at)}
					</p>
					<p class="mt-4 line-clamp-2 text-base leading-7 text-slate-700">
						{excerpt(post.content)}
					</p>
				</a>
			{/each}
		</section>

		{#if hasNoInitialPosts}
			<p
				class="rounded-lg border border-slate-200 bg-white p-10 text-center text-xl text-slate-600"
			>
				No posts found. Be the first to start a discussion!
			</p>
		{/if}

		{#if hasNoSearchResults}
			<p
				id="no-search-results"
				class="rounded-lg border border-red-200 bg-red-50 p-8 text-center text-lg text-red-900"
			>
				No discussions found matching your search. Try a different keyword.
			</p>
		{/if}

		{#if canLoadMore}
			<div class="text-center">
				<Button type="button" disabled={!isEnhanced} onclick={loadMorePosts}>
					Load 10 More Discussions
				</Button>
			</div>
		{/if}
	</div>
</PageShell>
