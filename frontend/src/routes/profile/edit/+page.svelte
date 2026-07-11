<script lang="ts">
	import { onMount } from 'svelte';
	import Alert from '$lib/components/Alert.svelte';
	import Button from '$lib/components/Button.svelte';
	import FormField from '$lib/components/FormField.svelte';
	import PageShell from '$lib/components/PageShell.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { apiFetch } from '$lib/api/client';
	import { normalizeStringOptions } from '$lib/api/options';
	import { routes } from '$lib/routes';
	import type { ActionData } from './$types';

	type StatusVariant = 'info' | 'success' | 'warning' | 'error';
	type StatusMessage = { variant: StatusVariant; message: string };
	type ApiMessage = { detail?: string; message?: string; url?: string };
	type MyInfoResponse = {
		state?: string;
		county?: string;
		district?: string;
		school?: string;
		teacher?: string;
		message?: string;
	};
	type TeacherProfile = {
		state?: string | null;
		county?: string | null;
		district?: string | null;
		school?: string | null;
		name?: string | null;
		wishlist_url?: string | null;
		about_me?: string | null;
	};
	let { form } = $props<{ form?: ActionData }>();

	const inputClass =
		'block min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-950 shadow-sm focus:border-green-600 focus:outline-2 focus:outline-green-600';

	let isLoadingProfile = $state(true);
	let isWishlistHelpOpen = $state(false);
	let isSubmitting = $state(false);
	let status = $state<StatusMessage | null>(null);
	let schoolOptionsStatus = $state<StatusMessage | null>(null);
	let formStatus = $derived(
		form?.message
			? {
					variant: (form.success ? 'success' : 'error') as StatusVariant,
					message: form.message
				}
			: null
	);

	let teacherName = $state('');
	let aboutMe = $state('');
	let wishlist = $state('');
	let urlId = $state('');
	let states = $state<string[]>([]);
	let counties = $state<string[]>([]);
	let districts = $state<string[]>([]);
	let schools = $state<string[]>([]);
	let selectedState = $state('');
	let selectedCounty = $state('');
	let selectedDistrict = $state('');
	let selectedSchool = $state('');

	let charactersRemaining = $derived(500 - aboutMe.length);

	onMount(() => {
		void initializeEditPage();
	});

	async function initializeEditPage() {
		isLoadingProfile = true;
		status = { variant: 'info', message: 'Loading your teacher profile...' };

		try {
			await Promise.all([loadStates(), loadTeacherProfile()]);
			status = null;
		} catch (error) {
			status = {
				variant: 'error',
				message:
					error instanceof Error
						? error.message
						: 'Teacher profile information could not be loaded.'
			};
		} finally {
			isLoadingProfile = false;
		}
	}

	async function loadTeacherProfile() {
		const myInfo = await apiFetch<MyInfoResponse>('/profile/myinfo/');
		if (myInfo.message && !myInfo.teacher) {
			throw new Error(myInfo.message);
		}

		selectedState = myInfo.state || '';
		selectedCounty = myInfo.county || '';
		selectedDistrict = myInfo.district || '';
		selectedSchool = myInfo.school || '';
		teacherName = myInfo.teacher || '';

		await loadDependentSchoolOptions();

		try {
			const teacherInfo = await apiFetch<TeacherProfile>('/api/get_teacher_info/');
			teacherName = teacherInfo.name || teacherName;
			aboutMe = teacherInfo.about_me || '';
			wishlist = teacherInfo.wishlist_url || '';
			selectedState = teacherInfo.state || selectedState;
			selectedCounty = teacherInfo.county || selectedCounty;
			selectedDistrict = teacherInfo.district || selectedDistrict;
			selectedSchool = teacherInfo.school || selectedSchool;
			await loadDependentSchoolOptions();
		} catch {
			// The profile form can still render from myinfo if the public teacher payload is unavailable.
		}

		await loadTeacherUrlId();
	}

	async function loadTeacherUrlId() {
		try {
			const body = await apiFetch<ApiMessage>('/api/teacher_url/');
			urlId = body.url?.split('/teacher/').pop() || '';
		} catch (error) {
			console.error('Error loading teacher URL ID:', error);
		}
	}

	async function loadStates() {
		try {
			states = mergeOptions(
				await fetchSchoolOptions('/api/get_states/'),
				selectedState ? [selectedState] : []
			);
			schoolOptionsStatus = null;
		} catch (error) {
			schoolOptionsStatus = {
				variant: 'warning',
				message:
					error instanceof Error ? error.message : 'School choices are temporarily unavailable.'
			};
		}
	}

	async function loadDependentSchoolOptions() {
		if (selectedState) {
			counties = mergeOptions(
				await fetchSchoolOptions(`/api/get_counties/${encodeURIComponent(selectedState)}`),
				selectedCounty ? [selectedCounty] : []
			);
		}

		if (selectedState && selectedCounty) {
			districts = mergeOptions(
				await fetchSchoolOptions(
					`/api/get_districts/${encodeURIComponent(selectedState)}/${encodeURIComponent(
						selectedCounty
					)}`
				),
				selectedDistrict ? [selectedDistrict] : []
			);
		}

		if (selectedState && selectedCounty && selectedDistrict) {
			schools = mergeOptions(
				await fetchSchoolOptions(
					`/api/get_schools/${encodeURIComponent(selectedState)}/${encodeURIComponent(
						selectedCounty
					)}/${encodeURIComponent(selectedDistrict)}`
				),
				selectedSchool ? [selectedSchool] : []
			);
		}
	}

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

	async function fetchSchoolOptions(path: string): Promise<string[]> {
		const body = await apiFetch<unknown>(path);
		return normalizeStringOptions(body);
	}

	function mergeOptions(primary: string[], fallback: string[]): string[] {
		return Array.from(new Set([...fallback, ...primary].filter(Boolean))).sort();
	}

	async function submitForm(event: SubmitEvent, endpoint: string, successFallback: string) {
		event.preventDefault();

		const form = event.currentTarget;
		if (!(form instanceof HTMLFormElement)) {
			return;
		}

		isSubmitting = true;
		status = { variant: 'info', message: 'Submitting your update...' };

		try {
			const body = await apiFetch<ApiMessage>(endpoint, {
				method: 'POST',
				body: new FormData(form)
			});
			const message = body.detail || body.message;

			status = {
				variant: 'success',
				message: message || successFallback
			};
			window.location.href = routes.teacher;
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
	title="Edit Teacher Profile - Homeroom Heroes"
	description="Edit your Homeroom Heroes teacher profile details, school, wishlist, and share URL."
	path={routes.profileEdit}
	noindex
/>

<PageShell eyebrow="Teacher Profile" title="Edit Teacher Profile" narrow>
	<div class="mx-auto max-w-2xl">
		<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
			{#if status || formStatus}
				<div class="mb-6">
					{#if status}
						<Alert variant={status.variant}>{status.message}</Alert>
					{:else if formStatus}
						<Alert variant={formStatus.variant}>{formStatus.message}</Alert>
					{/if}
				</div>
			{/if}

			{#if schoolOptionsStatus}
				<div class="mb-6">
					<Alert variant={schoolOptionsStatus.variant}>{schoolOptionsStatus.message}</Alert>
				</div>
			{/if}

			{#if isLoadingProfile}
				<p class="text-sm text-slate-700">Loading profile editor...</p>
			{:else}
				<div class="space-y-8">
					<form
						action="?/updateName"
						method="post"
						enctype="multipart/form-data"
						class="space-y-4"
						onsubmit={(event) =>
							submitForm(event, '/profile/update_teacher_name/', 'Name updated.')}
					>
						<h2 class="text-2xl font-semibold tracking-normal text-green-800">Update Name</h2>
						<FormField id="teacherName" label="Name" required>
							<input
								id="teacherName"
								name="teacher"
								type="text"
								required
								class={inputClass}
								bind:value={teacherName}
							/>
						</FormField>
						<Button type="submit" disabled={isSubmitting} class="w-full">Update Name</Button>
					</form>

					<hr class="border-slate-200" />

					<form
						action="?/updateSchool"
						method="post"
						enctype="multipart/form-data"
						class="space-y-4"
						onsubmit={(event) =>
							submitForm(
								event,
								'/profile/update_teacher_school/',
								'School information updated successfully.'
							)}
					>
						<h2 class="text-2xl font-semibold tracking-normal text-green-800">Update School</h2>
						<div class="grid gap-4 md:grid-cols-2">
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
						</div>

						<div class="grid gap-4 md:grid-cols-2">
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
						</div>

						<Button type="submit" disabled={isSubmitting} class="w-full">Update School</Button>
					</form>

					<hr class="border-slate-200" />

					<form
						action="?/updateInfo"
						method="post"
						enctype="multipart/form-data"
						class="space-y-4"
						onsubmit={(event) => submitForm(event, '/profile/update_info/', 'Info updated.')}
					>
						<h2 class="text-2xl font-semibold tracking-normal text-green-800">Update About Me</h2>
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
								rows="4"
								required
								class={`${inputClass} resize-y`}
								bind:value={aboutMe}></textarea>
						</FormField>
						<Button type="submit" disabled={isSubmitting} class="w-full">Update About Me</Button>
					</form>

					<hr class="border-slate-200" />

					<form
						action="?/updateWishlist"
						method="post"
						enctype="multipart/form-data"
						class="space-y-4"
						onsubmit={(event) =>
							submitForm(event, '/profile/update_wishlist/', 'Wishlist updated.')}
					>
						<h2 class="text-2xl font-semibold tracking-normal text-green-800">Update Wishlist</h2>
						<FormField
							id="wishlist"
							label="Amazon Wishlist URL"
							help="If you need help, follow our directions to ensure that your link works. Registry links do not work."
							required
						>
							<div class="space-y-3">
								<Button
									type="button"
									variant="secondary"
									onclick={() => (isWishlistHelpOpen = true)}
								>
									How to Get Link
								</Button>
								<input
									id="wishlist"
									name="wishlist"
									type="url"
									required
									class={inputClass}
									bind:value={wishlist}
								/>
							</div>
						</FormField>
						<Button type="submit" disabled={isSubmitting} class="w-full">Update Wishlist</Button>
					</form>

					<hr class="border-slate-200" />

					<form
						action="?/updateUrlId"
						method="post"
						enctype="multipart/form-data"
						class="space-y-4"
						onsubmit={(event) =>
							submitForm(event, '/profile/update_url_id/', 'URL ID updated successfully.')}
					>
						<h2 class="text-2xl font-semibold tracking-normal text-green-800">Update URL ID</h2>
						<p class="text-sm leading-6 text-slate-600">
							The URL ID is your unique marker for your page when using the Share button.
						</p>
						<p class="text-sm leading-6 text-slate-600">
							The format is:
							<span class="font-mono text-slate-800">www.HelpTeachers.net/teacher/{'{url id}'}</span
							>
						</p>
						<FormField id="url_id" label="URL ID" required>
							<input
								id="url_id"
								name="url_id"
								type="text"
								required
								class={inputClass}
								bind:value={urlId}
							/>
						</FormField>
						<Button type="submit" disabled={isSubmitting} class="w-full">Update URL ID</Button>
					</form>
				</div>
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
