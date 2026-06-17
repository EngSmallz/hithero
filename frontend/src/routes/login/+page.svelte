<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import Alert from '$lib/components/Alert.svelte';
	import Button from '$lib/components/Button.svelte';
	import FormField from '$lib/components/FormField.svelte';
	import PageShell from '$lib/components/PageShell.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { getBackendOrigin } from '$lib/api/client';
	import type { UserRole } from '$lib/api/types';
	import { routes } from '$lib/routes';

	type StatusVariant = 'info' | 'success' | 'warning' | 'error';
	type LoginResponse = {
		message?: string;
		createCount?: number;
		role?: UserRole;
	};

	const backendOrigin = getBackendOrigin();
	const loginEndpoint = `${backendOrigin}/profile/login/`;
	const inputClass =
		'block min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-950 shadow-sm focus:border-green-600 focus:outline-2 focus:outline-green-600';

	let isSubmitting = $state(false);
	let status = $state<{ variant: StatusVariant; message: string } | null>(null);

	async function submitLoginForm(event: SubmitEvent) {
		event.preventDefault();

		const form = event.currentTarget;
		if (!(form instanceof HTMLFormElement)) {
			return;
		}

		isSubmitting = true;
		status = { variant: 'info', message: 'Signing you in...' };

		try {
			const response = await fetch(loginEndpoint, {
				method: 'POST',
				body: new FormData(form),
				credentials: 'include'
			});
			const body = (await response.json().catch(() => ({}))) as LoginResponse;
			const message = body.message || 'Login failed. Please check your credentials and try again.';

			if (!response.ok) {
				throw new Error(message);
			}

			if (!body.role) {
				status = {
					variant: 'warning',
					message
				};
				return;
			}

			status = {
				variant: 'success',
				message
			};

			if (body.role === 'teacher' && body.createCount === 0) {
				await goto(resolve(routes.profileCreate as '/'));
				return;
			}

			await goto(resolve(routes.home));
		} catch (error) {
			status = {
				variant: 'error',
				message:
					error instanceof Error
						? error.message
						: 'An error occurred during login. Please try again.'
			};
		} finally {
			isSubmitting = false;
		}
	}
</script>

<Seo
	title="Homeroom Heroes - Login"
	description="Log in to your Homeroom Heroes account to manage your teacher profile, wishlist, and account activity."
	path={routes.login}
/>

<PageShell
	eyebrow="Account"
	title="Log In to Your Account"
	intro="Access your Homeroom Heroes account to manage your teacher profile and wishlist."
>
	<div class="mx-auto max-w-md">
		<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
			<form
				action={loginEndpoint}
				method="post"
				enctype="multipart/form-data"
				class="space-y-5"
				onsubmit={submitLoginForm}
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

				<FormField id="password" label="Password" required>
					<input
						id="password"
						name="password"
						type="password"
						autocomplete="current-password"
						required
						class={inputClass}
					/>
				</FormField>

				<Button type="submit" disabled={isSubmitting} class="w-full">
					{isSubmitting ? 'Signing In...' : 'Submit'}
				</Button>
			</form>

			<div class="mt-6 flex flex-col gap-3 text-center sm:flex-row">
				<Button href={routes.forgot} variant="ghost" class="w-full">Forgot Password</Button>
				<Button href={routes.register} variant="secondary" class="w-full">Register</Button>
			</div>

			{#if status}
				<div class="mt-5">
					<Alert variant={status.variant}>{status.message}</Alert>
				</div>
			{/if}
		</section>
	</div>
</PageShell>
