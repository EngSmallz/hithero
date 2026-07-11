<script lang="ts">
	import { page } from '$app/state';
	import Alert from '$lib/components/Alert.svelte';
	import Button from '$lib/components/Button.svelte';
	import FormField from '$lib/components/FormField.svelte';
	import PageShell from '$lib/components/PageShell.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { getBackendOrigin } from '$lib/api/client';
	import { routes } from '$lib/routes';
	import type { ActionData } from './$types';

	type StatusVariant = 'info' | 'success' | 'warning' | 'error';
	type StatusMessage = { variant: StatusVariant; message: string };
	type ApiMessage = { detail?: string; message?: string };

	const backendOrigin = getBackendOrigin();
	const resetPasswordEndpoint = `${backendOrigin}/profile/reset_password/`;
	const inputClass =
		'block min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-950 shadow-sm focus:border-green-600 focus:outline-2 focus:outline-green-600';

	let token = $derived(page.url.searchParams.get('token') ?? '');
	let isSubmitting = $state(false);
	let hasResetPassword = $state(false);
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

	async function submitResetPasswordForm(event: SubmitEvent) {
		event.preventDefault();

		const form = event.currentTarget;
		if (!(form instanceof HTMLFormElement)) {
			return;
		}

		const formData = new FormData(form);
		const newPassword = String(formData.get('new_password') ?? '');
		const confirmPassword = String(formData.get('confirm_password') ?? '');

		if (newPassword !== confirmPassword) {
			status = { variant: 'warning', message: 'Passwords do not match.' };
			return;
		}

		isSubmitting = true;
		status = { variant: 'info', message: 'Resetting your password...' };

		try {
			const response = await fetch(resetPasswordEndpoint, {
				method: 'POST',
				body: formData
			});
			const body = (await response.json().catch(() => ({}))) as ApiMessage;
			const message = body.detail || body.message;

			if (!response.ok) {
				throw new Error(message || 'Something went wrong. Please try again.');
			}

			hasResetPassword = true;
			status = {
				variant: 'success',
				message: message || 'Password reset successfully. You can now log in.'
			};
		} catch (error) {
			status = {
				variant: 'error',
				message: error instanceof Error ? error.message : 'An error occurred. Please try again.'
			};
		} finally {
			isSubmitting = false;
		}
	}
</script>

<Seo
	title="Reset Password - Homeroom Heroes"
	description="Reset your Homeroom Heroes account password using your secure reset link."
	path={routes.resetPassword}
	noindex
/>

<PageShell
	eyebrow="Account Help"
	title="Reset Your Password"
	intro="Create a new password for your Homeroom Heroes account."
	narrow
>
	<div class="mx-auto max-w-md">
		{#if hasResetPassword || form?.success}
			<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
				<h2 class="text-3xl font-bold tracking-normal text-green-800">Password Reset!</h2>
				{#if status || formStatus}
					<div class="mt-5">
						{#if status}
							<Alert variant={status.variant}>{status.message}</Alert>
						{:else if formStatus}
							<Alert variant={formStatus.variant}>{formStatus.message}</Alert>
						{/if}
					</div>
				{/if}
				<Button href={routes.login} class="mt-6 w-full">Go to Login</Button>
			</section>
		{:else if !token}
			<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
				<h2 class="text-3xl font-bold tracking-normal text-red-700">Invalid Reset Link</h2>
				<p class="mt-4 text-base leading-7 text-slate-700">
					This password reset link is missing, invalid, or has already expired. Please request a new
					one.
				</p>
				<div class="mt-6 flex flex-col gap-3 text-center sm:flex-row">
					<Button href={routes.login} class="w-full">Back to Login</Button>
					<Button href={routes.forgot} variant="secondary" class="w-full">Request New Link</Button>
				</div>
			</section>
		{:else}
			<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
				<form
					method="post"
					enctype="multipart/form-data"
					class="space-y-5"
					onsubmit={submitResetPasswordForm}
				>
					<input type="hidden" id="token" name="token" value={token} />

					<FormField id="new_password" label="New Password" required>
						<input
							id="new_password"
							name="new_password"
							type="password"
							autocomplete="new-password"
							required
							class={inputClass}
						/>
					</FormField>

					<FormField id="confirm_password" label="Confirm New Password" required>
						<input
							id="confirm_password"
							name="confirm_password"
							type="password"
							autocomplete="new-password"
							required
							class={inputClass}
						/>
					</FormField>

					<Button type="submit" disabled={isSubmitting} class="w-full">
						{isSubmitting ? 'Resetting...' : 'Reset Password'}
					</Button>
				</form>

				<div class="mt-6 text-center">
					<Button href={routes.login} variant="ghost" class="w-full">Back to Login</Button>
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
		{/if}
	</div>
</PageShell>
