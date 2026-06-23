<script lang="ts">
	import Alert from '$lib/components/Alert.svelte';
	import Button from '$lib/components/Button.svelte';
	import FormField from '$lib/components/FormField.svelte';
	import PageShell from '$lib/components/PageShell.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { getBackendOrigin } from '$lib/api/client';
	import { normalizeStringOptions } from '$lib/api/options';
	import { routes } from '$lib/routes';
	import type { PageData } from './$types';

	type ApiMessage = { detail?: string; message?: string };
	type StatusVariant = 'info' | 'success' | 'warning' | 'error';
	type StatusMessage = { variant: StatusVariant; message: string };

	let { data } = $props<{ data: PageData }>();

	const backendOrigin = getBackendOrigin();
	const inputClass =
		'block min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-950 shadow-sm focus:border-green-600 focus:outline-2 focus:outline-green-600 disabled:bg-slate-100 disabled:text-slate-500';

	let states = $derived(data.states);
	let counties = $state<string[]>([]);
	let districts = $state<string[]>([]);
	let schools = $state<string[]>([]);
	let selectedState = $state('');
	let selectedCounty = $state('');
	let selectedDistrict = $state('');
	let reportStatus = $derived<StatusMessage | null>(
		data.backendUnavailable
			? {
					variant: 'warning',
					message: 'School choices are temporarily unavailable.'
				}
			: null
	);
	let deleteStatus = $state<StatusMessage | null>(null);
	let isReportSubmitting = $state(false);
	let isDeleteSubmitting = $state(false);

	$effect(() => {
		states = data.states;
	});

	async function fetchOptions(path: string): Promise<string[]> {
		const response = await fetch(`${backendOrigin}${path}`, {
			credentials: 'include'
		});
		const body = (await response.json().catch(() => [])) as string[] | ApiMessage;

		if (!response.ok || !Array.isArray(body)) {
			const message = Array.isArray(body) ? undefined : body.detail || body.message;
			throw new Error(message || 'Unable to load school choices.');
		}

		return normalizeStringOptions(body);
	}

	async function populateCounties() {
		selectedCounty = '';
		selectedDistrict = '';
		counties = [];
		districts = [];
		schools = [];

		if (!selectedState) {
			return;
		}

		try {
			counties = await fetchOptions(`/api/index_counties/${encodeURIComponent(selectedState)}`);
		} catch (error) {
			reportStatus = {
				variant: 'error',
				message: error instanceof Error ? error.message : 'Unable to load county choices.'
			};
		}
	}

	async function populateDistricts() {
		selectedDistrict = '';
		districts = [];
		schools = [];

		if (!selectedState || !selectedCounty) {
			return;
		}

		try {
			districts = await fetchOptions(
				`/api/index_districts/${encodeURIComponent(selectedState)}/${encodeURIComponent(selectedCounty)}`
			);
		} catch (error) {
			reportStatus = {
				variant: 'error',
				message: error instanceof Error ? error.message : 'Unable to load district choices.'
			};
		}
	}

	async function populateSchools() {
		schools = [];

		if (!selectedState || !selectedCounty || !selectedDistrict) {
			return;
		}

		try {
			schools = await fetchOptions(
				`/api/index_schools/${encodeURIComponent(selectedState)}/${encodeURIComponent(selectedCounty)}/${encodeURIComponent(selectedDistrict)}`
			);
		} catch (error) {
			reportStatus = {
				variant: 'error',
				message: error instanceof Error ? error.message : 'Unable to load school choices.'
			};
		}
	}

	async function submitTeacherReport(event: SubmitEvent) {
		event.preventDefault();

		const form = event.currentTarget;
		if (!(form instanceof HTMLFormElement)) {
			return;
		}

		isReportSubmitting = true;
		reportStatus = { variant: 'info', message: 'Generating teacher report...' };

		try {
			const response = await fetch(`${backendOrigin}/admin/generate_teacher_report/`, {
				method: 'POST',
				body: new FormData(form),
				credentials: 'include'
			});
			const body = (await response.json().catch(() => ({}))) as ApiMessage;

			if (!response.ok) {
				throw new Error(body.detail || body.message || 'Failed to generate teacher report.');
			}

			reportStatus = {
				variant: 'success',
				message: body.message || 'Teacher report saved and sent via email.'
			};
		} catch (error) {
			reportStatus = {
				variant: 'error',
				message: error instanceof Error ? error.message : 'Failed to generate teacher report.'
			};
		} finally {
			isReportSubmitting = false;
		}
	}

	async function submitDeleteUser(event: SubmitEvent) {
		event.preventDefault();

		const form = event.currentTarget;
		if (!(form instanceof HTMLFormElement)) {
			return;
		}

		const formData = new FormData(form);
		const targetEmail = String(formData.get('target_email') || '');
		if (
			!window.confirm(
				`Are you sure you want to delete user: ${targetEmail}? This action cannot be undone.`
			)
		) {
			return;
		}

		isDeleteSubmitting = true;
		deleteStatus = { variant: 'info', message: 'Deleting user account...' };

		try {
			const response = await fetch(`${backendOrigin}/profile/delete/`, {
				method: 'POST',
				body: formData,
				credentials: 'include'
			});
			const body = (await response.json().catch(() => ({}))) as ApiMessage;

			if (!response.ok) {
				throw new Error(body.detail || body.message || 'Failed to delete user.');
			}

			deleteStatus = {
				variant: 'success',
				message: body.message || `Successfully deleted account for target user: ${targetEmail}.`
			};
			form.reset();
		} catch (error) {
			deleteStatus = {
				variant: 'error',
				message: error instanceof Error ? error.message : 'Failed to delete user.'
			};
		} finally {
			isDeleteSubmitting = false;
		}
	}
</script>

<Seo
	title="Admin Panel - Homeroom Heroes"
	description="Homeroom Heroes administrator tools."
	path={routes.admin}
	noindex
/>

<PageShell
	eyebrow="Admin"
	title="Admin Panel"
	intro="Generate teacher contact reports and manage user accounts."
>
	<div class="mx-auto grid max-w-5xl gap-8">
		<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
			<h2 class="text-3xl font-bold tracking-normal text-green-800">Get Teacher Contact Info</h2>
			<form class="mt-6 space-y-6" onsubmit={submitTeacherReport}>
				<div class="grid gap-5 md:grid-cols-2">
					<FormField id="state" label="State" required>
						<select
							id="state"
							name="state"
							required
							class={inputClass}
							bind:value={selectedState}
							onchange={populateCounties}
						>
							<option value="" disabled>Choose state</option>
							{#each states as state (state)}
								<option value={state}>{state}</option>
							{/each}
						</select>
					</FormField>

					<FormField id="county" label="County">
						<select
							id="county"
							name="county"
							class={inputClass}
							bind:value={selectedCounty}
							disabled={!selectedState}
							onchange={populateDistricts}
						>
							<option value="">Choose county</option>
							{#each counties as county (county)}
								<option value={county}>{county}</option>
							{/each}
						</select>
					</FormField>
				</div>

				<div class="grid gap-5 md:grid-cols-2">
					<FormField id="district" label="School District">
						<select
							id="district"
							name="district"
							class={inputClass}
							bind:value={selectedDistrict}
							disabled={!selectedCounty}
							onchange={populateSchools}
						>
							<option value="">Choose district</option>
							{#each districts as district (district)}
								<option value={district}>{district}</option>
							{/each}
						</select>
					</FormField>

					<FormField id="school" label="School">
						<select id="school" name="school" class={inputClass} disabled={!selectedDistrict}>
							<option value="">Choose school</option>
							{#each schools as school (school)}
								<option value={school}>{school}</option>
							{/each}
						</select>
					</FormField>
				</div>

				<Button type="submit" disabled={isReportSubmitting}>
					{isReportSubmitting ? 'Generating...' : 'Get Info'}
				</Button>
			</form>

			{#if reportStatus}
				<div class="mt-5">
					<Alert variant={reportStatus.variant}>{reportStatus.message}</Alert>
				</div>
			{/if}
		</section>

		<section class="rounded-lg border border-red-200 bg-white p-6 shadow-sm sm:p-8">
			<h2 class="text-3xl font-bold tracking-normal text-red-700">Delete User Account</h2>
			<form class="mt-6 space-y-5" onsubmit={submitDeleteUser}>
				<FormField id="target_email" label="Target User Email" required>
					<input
						id="target_email"
						name="target_email"
						type="email"
						required
						placeholder="user.to.delete@example.com"
						class={inputClass}
					/>
				</FormField>

				<FormField id="admin_secret_input" label="Admin Secret Key" required>
					<input
						id="admin_secret_input"
						name="admin_secret_input"
						type="password"
						required
						placeholder="Enter admin secret"
						class={inputClass}
					/>
				</FormField>

				<Button type="submit" disabled={isDeleteSubmitting}>
					{isDeleteSubmitting ? 'Deleting...' : 'Permanently Delete Account'}
				</Button>
			</form>

			{#if deleteStatus}
				<div class="mt-5">
					<Alert variant={deleteStatus.variant}>{deleteStatus.message}</Alert>
				</div>
			{/if}
		</section>
	</div>
</PageShell>
