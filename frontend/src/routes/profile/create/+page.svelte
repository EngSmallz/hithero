<script lang="ts">
	import Alert from '$lib/components/Alert.svelte';
	import Button from '$lib/components/Button.svelte';
	import FormField from '$lib/components/FormField.svelte';
	import PageShell from '$lib/components/PageShell.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { apiFetch } from '$lib/api/client';
	import { normalizeStringOptions } from '$lib/api/options';
	import { routes } from '$lib/routes';
	import type { UserRole } from '$lib/api/types';
	import type { ActionData, PageData } from './$types';

	type StatusVariant = 'info' | 'success' | 'warning' | 'error';
	type StatusMessage = { variant: StatusVariant; message: string };
	type ApiMessage = { detail?: string; message?: string; role?: UserRole };
	let { data, form } = $props<{ data: PageData; form?: ActionData }>();

	const inputClass =
		'block min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-950 shadow-sm focus:border-green-600 focus:outline-2 focus:outline-green-600';

	let states = $derived(data.states);
	let counties = $state<string[]>([]);
	let districts = $state<string[]>([]);
	let schools = $state<string[]>([]);
	let selectedState = $state('');
	let selectedCounty = $state('');
	let selectedDistrict = $state('');
	let selectedSchool = $state('');
	let aboutMe = $state('');
	let isWishlistHelpOpen = $state(false);
	let isSubmitting = $state(false);
	let hasCreatedProfile = $state(false);
	let status = $state<StatusMessage | null>(null);
	let schoolOptionsStatus = $state<StatusMessage | null>(null);
	let hasInitializedSchoolOptionsStatus = $state(false);
	let formStatus = $derived(
		form?.message
			? {
					variant: (form.success ? 'success' : 'error') as StatusVariant,
					message: form.message
				}
			: null
	);

	let charactersRemaining = $derived(500 - aboutMe.length);

	$effect(() => {
		if (hasInitializedSchoolOptionsStatus) {
			return;
		}

		hasInitializedSchoolOptionsStatus = true;
		if (data.backendUnavailable) {
			schoolOptionsStatus = {
				variant: 'warning',
				message:
					'School choices are temporarily unavailable. Please try again shortly, or contact us if your school is not listed.'
			};
		}
	});

	function resetCountySelection() {
		selectedCounty = '';
		selectedDistrict = '';
		selectedSchool = '';
		counties = [];
		districts = [];
		schools = [];
	}

	function resetDistrictSelection() {
		selectedDistrict = '';
		selectedSchool = '';
		districts = [];
		schools = [];
	}

	function resetSchoolSelection() {
		selectedSchool = '';
		schools = [];
	}

	async function fetchSchoolOptions(path: string): Promise<string[]> {
		const body = await apiFetch<unknown>(path);
		return normalizeStringOptions(body);
	}

	async function handleStateChange() {
		resetCountySelection();

		if (!selectedState) {
			return;
		}

		try {
			counties = await fetchSchoolOptions(`/api/get_counties/${encodeURIComponent(selectedState)}`);
			schoolOptionsStatus = null;
		} catch (error) {
			schoolOptionsStatus = {
				variant: 'error',
				message: error instanceof Error ? error.message : 'County options could not be loaded.'
			};
		}
	}

	async function handleCountyChange() {
		resetDistrictSelection();

		if (!selectedState || !selectedCounty) {
			return;
		}

		try {
			districts = await fetchSchoolOptions(
				`/api/get_districts/${encodeURIComponent(selectedState)}/${encodeURIComponent(selectedCounty)}`
			);
			schoolOptionsStatus = null;
		} catch (error) {
			schoolOptionsStatus = {
				variant: 'error',
				message: error instanceof Error ? error.message : 'District options could not be loaded.'
			};
		}
	}

	async function handleDistrictChange() {
		resetSchoolSelection();

		if (!selectedState || !selectedCounty || !selectedDistrict) {
			return;
		}

		try {
			schools = await fetchSchoolOptions(
				`/api/get_schools/${encodeURIComponent(selectedState)}/${encodeURIComponent(
					selectedCounty
				)}/${encodeURIComponent(selectedDistrict)}`
			);
			schoolOptionsStatus = null;
		} catch (error) {
			schoolOptionsStatus = {
				variant: 'error',
				message: error instanceof Error ? error.message : 'School options could not be loaded.'
			};
		}
	}

	async function submitCreateProfileForm(event: SubmitEvent) {
		event.preventDefault();

		const form = event.currentTarget;
		if (!(form instanceof HTMLFormElement)) {
			return;
		}

		isSubmitting = true;
		status = { variant: 'info', message: 'Creating your teacher profile...' };

		try {
			const body = await apiFetch<ApiMessage>('/profile/create_teacher_profile/', {
				method: 'POST',
				body: new FormData(form)
			});
			const message = body.detail || body.message;

			const createdProfile = body.role === 'teacher' || body.role === 'admin';
			hasCreatedProfile = createdProfile;
			status = {
				variant: createdProfile ? 'success' : 'warning',
				message: message || 'Teacher created successfully'
			};
		} catch (error) {
			status = {
				variant: 'error',
				message:
					error instanceof Error
						? error.message
						: 'An error occurred during profile creation. Please try again.'
			};
		} finally {
			isSubmitting = false;
		}
	}

	async function openMyPage() {
		try {
			await apiFetch<unknown>('/profile/myinfo/');
		} finally {
			window.location.href = routes.teacher;
		}
	}
</script>

<Seo
	title="Homeroom Heroes - Create Teacher Profile"
	description="Create your Homeroom Heroes teacher profile and share your classroom wishlist."
	path={routes.profileCreate}
	noindex
/>

<PageShell
	eyebrow="Teacher Profile"
	title="Create Teacher Profile"
	intro="Add the details supporters will use to find your classroom and wishlist."
	narrow
>
	<div class="mx-auto max-w-3xl">
		<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
			{#if hasCreatedProfile || form?.success}
				<div class="space-y-5">
					{#if status || formStatus}
						{#if status}
							<Alert variant={status.variant}>{status.message}</Alert>
						{:else if formStatus}
							<Alert variant={formStatus.variant}>{formStatus.message}</Alert>
						{/if}
					{/if}
					<Button onclick={openMyPage} class="w-full sm:w-auto">View My Page</Button>
				</div>
			{:else}
				{#if schoolOptionsStatus}
					<div class="mb-5">
						<Alert variant={schoolOptionsStatus.variant}>{schoolOptionsStatus.message}</Alert>
					</div>
				{/if}

				<form
					action={routes.profileCreate}
					method="post"
					enctype="multipart/form-data"
					class="space-y-5"
					onsubmit={submitCreateProfileForm}
				>
					<FormField id="name" label="Full Name" required>
						<input
							id="name"
							name="name"
							type="text"
							autocomplete="name"
							required
							class={inputClass}
						/>
					</FormField>

					<FormField id="state" label="State" required>
						<select
							id="state"
							name="state"
							required
							class={inputClass}
							bind:value={selectedState}
							onchange={handleStateChange}
						>
							<option value="" disabled>Choose state</option>
							{#each states as state (state)}
								<option value={state}>{state}</option>
							{/each}
						</select>
					</FormField>

					<FormField id="county" label="County" required>
						<select
							id="county"
							name="county"
							required
							class={inputClass}
							bind:value={selectedCounty}
							onchange={handleCountyChange}
						>
							<option value="" disabled>Choose county</option>
							{#each counties as county (county)}
								<option value={county}>{county}</option>
							{/each}
						</select>
					</FormField>

					<FormField id="district" label="School District" required>
						<select
							id="district"
							name="district"
							required
							class={inputClass}
							bind:value={selectedDistrict}
							onchange={handleDistrictChange}
						>
							<option value="" disabled>Choose district</option>
							{#each districts as district (district)}
								<option value={district}>{district}</option>
							{/each}
						</select>
					</FormField>

					<FormField id="school" label="School" required>
						<select
							id="school"
							name="school"
							required
							class={inputClass}
							bind:value={selectedSchool}
						>
							<option value="" disabled>Choose school</option>
							{#each schools as school (school)}
								<option value={school}>{school}</option>
							{/each}
						</select>
					</FormField>

					<FormField
						id="aboutMe"
						label="About Me"
						help={`${charactersRemaining} characters remaining`}
						required
					>
						<textarea
							id="aboutMe"
							name="aboutMe"
							maxlength="500"
							rows="5"
							required
							class={`${inputClass} resize-y`}
							bind:value={aboutMe}></textarea>
					</FormField>

					<FormField
						id="wishlist"
						label="Amazon Wishlist URL"
						help="Registry links do not work. Use a shareable Amazon wishlist link."
						required
					>
						<div class="space-y-3">
							<Button type="button" variant="secondary" onclick={() => (isWishlistHelpOpen = true)}>
								How to Get Link
							</Button>
							<input id="wishlist" name="wishlist" type="url" required class={inputClass} />
						</div>
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
			{/if}
		</section>
	</div>
</PageShell>

{#if isWishlistHelpOpen}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4">
		<div
			role="dialog"
			aria-modal="true"
			aria-label="Wishlist setup"
			class="h-[85vh] w-full max-w-4xl rounded-lg bg-white p-4 shadow-xl"
		>
			<div class="mb-3 flex items-center justify-between gap-4">
				<h2 class="text-xl font-bold tracking-normal text-slate-950">Wishlist Setup</h2>
				<Button type="button" variant="ghost" onclick={() => (isWishlistHelpOpen = false)}>
					Close
				</Button>
			</div>
			<iframe
				src={routes.wishlistSetup}
				title="Wishlist setup"
				class="h-[calc(85vh-5rem)] w-full border-0"
			></iframe>
		</div>
	</div>
{/if}
