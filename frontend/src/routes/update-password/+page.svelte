<script lang="ts">
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
	type ApiMessage = { detail?: string; message?: string; status?: string };

	const backendOrigin = getBackendOrigin();
	const updatePasswordEndpoint = `${backendOrigin}/profile/update_password/`;
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

	async function submitUpdatePasswordForm(event: SubmitEvent) {
		event.preventDefault();

		const form = event.currentTarget;
		if (!(form instanceof HTMLFormElement)) {
			return;
		}

		isSubmitting = true;
		status = { variant: 'info', message: 'Updating your password...' };

		try {
			const response = await fetch(updatePasswordEndpoint, {
				method: 'POST',
				body: new FormData(form),
				credentials: 'include'
			});
			const body = (await response.json().catch(() => ({}))) as ApiMessage;
			const message = body.detail || body.message;

			if (!response.ok) {
				throw new Error(
					`Failed to update password: ${message || response.statusText}. Please try again.`
				);
			}

			if (body.status === 'success' || body.message === 'Password updated successfully') {
				status = {
					variant: 'success',
					message: 'Password updated successfully!'
				};
				window.location.href = routes.teacher;
				return;
			}

			status = {
				variant: 'warning',
				message: message || 'Password update did not complete. Please try again.'
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
	title="Update Password - Homeroom Heroes"
	description="Update the password for your Homeroom Heroes account."
	path={routes.updatePassword}
	noindex
/>

<PageShell eyebrow="Account" title="Update Your Password" narrow>
	<div class="mx-auto max-w-md">
		<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
			<form
				action={routes.updatePassword}
				method="post"
				enctype="multipart/form-data"
				class="space-y-5"
				onsubmit={submitUpdatePasswordForm}
			>
				<FormField id="old_password" label="Old Password" required>
					<input
						id="old_password"
						name="old_password"
						type="password"
						autocomplete="current-password"
						required
						class={inputClass}
					/>
				</FormField>

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

				<FormField id="new_password_confirmed" label="Confirm New Password" required>
					<input
						id="new_password_confirmed"
						name="new_password_confirmed"
						type="password"
						autocomplete="new-password"
						required
						class={inputClass}
					/>
				</FormField>

				<Button type="submit" disabled={isSubmitting} class="w-full">
					{isSubmitting ? 'Submitting...' : 'Submit'}
				</Button>
			</form>

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
