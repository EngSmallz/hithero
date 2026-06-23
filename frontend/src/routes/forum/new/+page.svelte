<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import Alert from '$lib/components/Alert.svelte';
	import Button from '$lib/components/Button.svelte';
	import FormField from '$lib/components/FormField.svelte';
	import PageShell from '$lib/components/PageShell.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { getBackendOrigin } from '$lib/api/client';
	import { routes } from '$lib/routes';

	type ApiMessage = { detail?: string; message?: string };
	type CreatedPost = { id?: number; detail?: string; message?: string };
	type StatusVariant = 'info' | 'success' | 'warning' | 'error';
	type StatusMessage = { variant: StatusVariant; message: string };

	const backendOrigin = getBackendOrigin();
	const createPostEndpoint = `${backendOrigin}/forum/create_post`;
	const inputClass =
		'block min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-950 shadow-sm focus:border-green-600 focus:outline-2 focus:outline-green-600';

	let isSubmitting = $state(false);
	let status = $state<StatusMessage | null>(null);

	async function submitPostForm(event: SubmitEvent) {
		event.preventDefault();

		const form = event.currentTarget;
		if (!(form instanceof HTMLFormElement)) {
			return;
		}

		isSubmitting = true;
		status = { variant: 'info', message: 'Creating your discussion...' };

		try {
			const response = await fetch(createPostEndpoint, {
				method: 'POST',
				body: new FormData(form),
				credentials: 'include'
			});
			const body = (await response.json().catch(() => ({}))) as CreatedPost | ApiMessage;
			const message = body.detail || body.message;

			if (!response.ok) {
				throw new Error(message || 'Could not create the discussion. Please try again.');
			}

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
			action={createPostEndpoint}
			method="post"
			enctype="multipart/form-data"
			class="space-y-5"
			onsubmit={submitPostForm}
		>
			<FormField id="title" label="Title" required>
				<input id="title" name="title" type="text" required maxlength="255" class={inputClass} />
			</FormField>

			<FormField id="content" label="Content" required>
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

		{#if status}
			<div class="mt-5">
				<Alert variant={status.variant}>{status.message}</Alert>
			</div>
		{/if}
	</section>
</PageShell>
