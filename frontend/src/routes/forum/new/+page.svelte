<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import Alert from '$lib/components/Alert.svelte';
	import Button from '$lib/components/Button.svelte';
	import FormField from '$lib/components/FormField.svelte';
	import PageShell from '$lib/components/PageShell.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { apiFetch } from '$lib/api/client';
	import { routes } from '$lib/routes';
	import type { ActionData } from './$types';

	type CreatedPost = { id?: number; detail?: string; message?: string };
	type StatusVariant = 'info' | 'success' | 'warning' | 'error';
	type StatusMessage = { variant: StatusVariant; message: string };

	let { form } = $props<{ form?: ActionData }>();

	const inputClass =
		'block min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-950 shadow-sm focus:border-green-600 focus:outline-2 focus:outline-green-600';

	let isSubmitting = $state(false);
	let status = $state<StatusMessage | null>(null);
	let serverStatus = $derived<StatusMessage | null>(
		form?.message
			? {
					variant: form.success ? 'success' : 'error',
					message: form.message
				}
			: null
	);

	async function submitPostForm(event: SubmitEvent) {
		event.preventDefault();

		const form = event.currentTarget;
		if (!(form instanceof HTMLFormElement)) {
			return;
		}

		isSubmitting = true;
		status = { variant: 'info', message: 'Creating your discussion...' };

		try {
			const body = await apiFetch<CreatedPost>('/forum/create_post', {
				method: 'POST',
				body: new FormData(form)
			});
			const message = body.detail || body.message;

			if ('id' in body && body.id) {
				status = { variant: 'success', message: 'Discussion created.' };
				await goto(resolve(`${routes.forumPost}?id=${encodeURIComponent(body.id)}` as '/'), {
					invalidateAll: true
				});
				return;
			}

			status = {
				variant: 'warning',
				message:
					message || 'Discussion created, but the new post could not be opened automatically.'
			};
		} catch (error) {
			status = {
				variant: 'error',
				message:
					error instanceof Error
						? error.message
						: 'An error occurred while creating the discussion.'
			};
		} finally {
			isSubmitting = false;
		}
	}
</script>

<Seo
	title="New Forum Discussion - Homeroom Heroes"
	description="Start a new Homeroom Heroes forum discussion."
	path={routes.forumNew}
	noindex
/>

<PageShell
	eyebrow="Forum"
	title="Create a New Discussion"
	intro="Share a classroom update, ask a question, or start a conversation with the Homeroom Heroes community."
	narrow
>
	<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
		<form
			action={resolve(routes.forumNew as '/')}
			method="post"
			enctype="multipart/form-data"
			class="space-y-5"
			onsubmit={submitPostForm}
		>
			<FormField id="title" label="Title" required>
				<input id="title" name="title" type="text" required maxlength="255" class={inputClass} />
			</FormField>

			<FormField
				id="content"
				label="Content"
				help="Supported HTML: <b>, <i>, <em>, <strong>, <a>, <p>, and <br>. Other tags and attributes are removed."
				required
			>
				<textarea
					id="content"
					name="content"
					required
					rows="10"
					class={`${inputClass} min-h-56 resize-y`}></textarea>
			</FormField>

			<div class="flex flex-col gap-3 sm:flex-row sm:items-center">
				<Button type="submit" disabled={isSubmitting}>
					{isSubmitting ? 'Creating...' : 'Create Post'}
				</Button>
				<Button href={routes.forum} variant="secondary">Back to Forum</Button>
			</div>
		</form>

		{#if status || serverStatus}
			<div class="mt-5 space-y-3">
				{#if serverStatus}
					<Alert variant={serverStatus.variant}>{serverStatus.message}</Alert>
				{/if}
				{#if form?.success && form.postId}
					{#if form.title}
						<p class="text-sm text-slate-700">
							Created: <span class="font-semibold text-slate-950">{form.title}</span>
						</p>
					{/if}
					<div class="flex flex-col gap-3 sm:flex-row">
						<Button href={`${routes.forumPost}?id=${encodeURIComponent(form.postId)}`}>
							Open Discussion
						</Button>
						<Button href={routes.forum} variant="secondary">Back to Forum</Button>
					</div>
				{/if}
				{#if status}
					<Alert variant={status.variant}>{status.message}</Alert>
				{/if}
			</div>
		{/if}
	</section>
</PageShell>
