<script lang="ts">
	import Alert from '$lib/components/Alert.svelte';
	import Button from '$lib/components/Button.svelte';
	import FormField from '$lib/components/FormField.svelte';
	import PageShell from '$lib/components/PageShell.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { apiFetch } from '$lib/api/client';
	import { routes } from '$lib/routes';
	import type { ActionData } from './$types';

	type StatusVariant = 'info' | 'success' | 'warning' | 'error';
	type StatusMessage = { variant: StatusVariant; message: string };
	type ApiMessage = { detail?: string; message?: string };

	const inputClass =
		'block min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-950 shadow-sm focus:border-green-600 focus:outline-2 focus:outline-green-600';

	let isSubmitting = $state(false);
	let status = $state<StatusMessage | null>(null);
	let { form } = $props<{ form?: ActionData }>();
	let formStatus = $derived(
		form?.message
			? {
					variant: (form.success ? 'success' : 'error') as StatusVariant,
					message: form.message
				}
			: null
	);

	async function submitForgotPasswordForm(event: SubmitEvent) {
		event.preventDefault();

		const form = event.currentTarget;
		if (!(form instanceof HTMLFormElement)) {
			return;
		}

		isSubmitting = true;
		status = { variant: 'info', message: 'Submitting your request...' };

		try {
			const body = await apiFetch<ApiMessage>('/profile/forgot_password/', {
				method: 'POST',
				body: new FormData(form)
			});
			const message = body.detail || body.message;

			status = {
				variant: 'success',
				message: message || 'If an account exists, a reset link will be sent to your email.'
			};
		} catch (error) {
			status = {
				variant: 'error',
				message:
					error instanceof Error ? error.message : 'A network error occurred. Please try again.'
			};
		} finally {
			isSubmitting = false;
		}
	}
</script>

<Seo
	title="Homeroom Heroes - Forgot Password"
	description="Request password reset instructions for your Homeroom Heroes account."
	path={routes.forgot}
	noindex
/>

<PageShell
	eyebrow="Account Help"
	title="Forgot Your Password?"
	intro="Enter your email address below, and we'll send instructions on how to reset your password."
	narrow
>
	<div class="mx-auto max-w-md">
		<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
			<form
				action={routes.forgot}
				method="post"
				enctype="multipart/form-data"
				class="space-y-5"
				onsubmit={submitForgotPasswordForm}
			>
				<FormField id="email" label="Email" required>
					<input
						id="email"
						name="email"
						type="email"
						autocomplete="email"
						required
						class={inputClass}
					/>
				</FormField>

				<Button type="submit" disabled={isSubmitting} class="w-full">
					{isSubmitting ? 'Submitting...' : 'Submit'}
				</Button>
			</form>

			<div class="mt-6 flex flex-col gap-3 text-center sm:flex-row">
				<Button href={routes.login} variant="ghost" class="w-full">Back to Login</Button>
				<Button href={routes.register} variant="secondary" class="w-full">Register</Button>
			</div>

			{#if status || formStatus}
				<div class="mt-5">
					{#if status}
						<Alert variant={status.variant}>{status.message}</Alert>
					{:else if formStatus}
						<Alert variant={formStatus.variant}>{formStatus.message}</Alert>
					{/if}
				</div>
			{/if}
		</section>
	</div>
</PageShell>
