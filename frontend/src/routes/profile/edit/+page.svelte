<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import { resolve } from '$app/paths';
	import Alert from '$lib/components/Alert.svelte';
	import Button from '$lib/components/Button.svelte';
	import FormField from '$lib/components/FormField.svelte';
	import PageShell from '$lib/components/PageShell.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { apiFetch } from '$lib/api/client';
	import { normalizeStringOptions } from '$lib/api/options';
	import { routes } from '$lib/routes';
	import type { ActionData, PageData } from './$types';

	type StatusVariant = 'info' | 'success' | 'warning' | 'error';
	type StatusMessage = { variant: StatusVariant; message: string };
	type ApiMessage = { detail?: string; message?: string; url?: string };
	let { data, form } = $props<{ data: PageData; form?: ActionData }>();

	const inputClass =
		'block min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-950 shadow-sm focus:border-green-600 focus:outline-2 focus:outline-green-600 disabled:cursor-not-allowed disabled:border-slate-300 disabled:bg-slate-100 disabled:text-slate-500 read-only:cursor-not-allowed read-only:border-slate-300 read-only:bg-slate-100 read-only:text-slate-700';
	const initialData = untrack(() => data);
	const schoolVerified = initialData.schoolVerified;
	const verifiedSchoolValues = {
		state: initialData.profile.state,
		county: initialData.profile.county,
		district: initialData.profile.district,
		school: initialData.profile.school
	};
	const schoolChangeWarning =
		'Confirm school change: your teacher profile will be removed from public and search results until the new school is reapproved. Continue?';

	let isEnhanced = $state(false);
	let isSchoolChangeEditing = $state(false);
	let isWishlistHelpOpen = $state(false);
	let isSubmitting = $state(false);
	let status = $state<StatusMessage | null>(null);
	let schoolOptionsStatus = $state<StatusMessage | null>(
		initialData.schoolOptionsUnavailable
			? {
					variant: 'warning',
					message:
						'School choices are temporarily unavailable. Your current values remain available.'
				}
			: null
	);
	let formStatus = $derived(
		form?.message
			? {
					variant: (form.success ? 'success' : 'error') as StatusVariant,
					message: form.message
				}
			: null
	);

	let teacherName = $state(initialData.profile.teacherName);
	let aboutMe = $state(initialData.profile.aboutMe);
	let wishlist = $state(initialData.profile.wishlist);
	let urlId = $state(initialData.profile.urlId);
	let states = $state<string[]>(initialData.schoolOptions.states);
	let counties = $state<string[]>(initialData.schoolOptions.counties);
	let districts = $state<string[]>(initialData.schoolOptions.districts);
	let schools = $state<string[]>(initialData.schoolOptions.schools);
	let selectedState = $state(initialData.profile.state);
	let selectedCounty = $state(initialData.profile.county);
	let selectedDistrict = $state(initialData.profile.district);
	let selectedSchool = $state(initialData.profile.school);

	let charactersRemaining = $derived(500 - aboutMe.length);

	onMount(() => {
		isEnhanced = true;
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

	function startSchoolChange() {
		if (!schoolVerified) {
			return;
		}
		selectedState = verifiedSchoolValues.state;
		selectedCounty = verifiedSchoolValues.county;
		selectedDistrict = verifiedSchoolValues.district;
		selectedSchool = verifiedSchoolValues.school;
		isSchoolChangeEditing = true;
	}

	function cancelSchoolChange() {
		selectedState = verifiedSchoolValues.state;
		selectedCounty = verifiedSchoolValues.county;
		selectedDistrict = verifiedSchoolValues.district;
		selectedSchool = verifiedSchoolValues.school;
		isSchoolChangeEditing = false;
	}

	function submitSchoolChange(event: SubmitEvent) {
		if (!window.confirm(schoolChangeWarning)) {
			event.preventDefault();
			return;
		}
		void submitForm(
			event,
			'/profile/request_school_change/',
			'School change submitted for reapproval.'
		);
	}

	function getSelectValue(event: Event): string {
		const target = event.currentTarget;
		return target instanceof HTMLSelectElement ? target.value : '';
	}

	async function handleStateChange(event: Event) {
		selectedState = getSelectValue(event);
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

	async function handleCountyChange(event: Event) {
		selectedCounty = getSelectValue(event);
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

	async function handleDistrictChange(event: Event) {
		selectedDistrict = getSelectValue(event);
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
		<section
			class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8"
			data-profile-enhanced={isEnhanced}
		>
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

			<div class="space-y-8">
				<form
					action="?/updateName"
					method="post"
					enctype="multipart/form-data"
					class="space-y-4"
					onsubmit={(event) => submitForm(event, '/profile/update_teacher_name/', 'Name updated.')}
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
					action={schoolVerified ? '?/requestSchoolChange' : '?/updateSchool'}
					method="post"
					enctype="multipart/form-data"
					class="space-y-4"
					onsubmit={(event) => {
						if (schoolVerified) {
							submitSchoolChange(event);
						} else {
							void submitForm(
								event,
								'/profile/update_teacher_school/',
								'School information updated successfully.'
							);
						}
					}}
				>
					<h2 class="text-2xl font-semibold tracking-normal text-green-800">Update School</h2>
					{#if !schoolVerified}
						<noscript>
						<style>
							.enhanced-school-fields {
								display: none;
							}
						</style>
						<div class="space-y-4">
							<div
								class="rounded-md border border-blue-200 bg-blue-50 p-4 text-blue-950"
								role="status"
							>
								JavaScript is disabled. Enter the complete school location below; this update will
								still submit through the Homeroom Heroes page.
							</div>
							<label class="block font-semibold text-slate-800" for="manual-edit-state">
								State (manual entry)
							</label>
							<input
								id="manual-edit-state"
								name="state"
								required
								class={inputClass}
								value={selectedState}
							/>
							<label class="block font-semibold text-slate-800" for="manual-edit-county">
								County (manual entry)
							</label>
							<input
								id="manual-edit-county"
								name="county"
								required
								class={inputClass}
								value={selectedCounty}
							/>
							<label class="block font-semibold text-slate-800" for="manual-edit-district">
								School District (manual entry)
							</label>
							<input
								id="manual-edit-district"
								name="district"
								required
								class={inputClass}
								value={selectedDistrict}
							/>
							<label class="block font-semibold text-slate-800" for="manual-edit-school">
								School (manual entry)
							</label>
							<input
								id="manual-edit-school"
								name="school"
								required
								class={inputClass}
								value={selectedSchool}
							/>
						</div>
						</noscript>
					{/if}

					{#if schoolVerified}
						<div
							class={`rounded-md border p-4 text-sm ${
								isSchoolChangeEditing
									? 'border-amber-200 bg-amber-50 text-amber-950'
									: 'border-green-200 bg-green-50 text-green-950'
							}`}
							aria-describedby="verified-school-note"
						>
							<p id="verified-school-note">
								{#if isSchoolChangeEditing}
									Changing your school will remove your teacher profile from public and search results
									until the new school is reapproved.
								{:else}
									School information was verified during registration and is read-only unless you
									start the school-change request flow below.
								{/if}
							</p>
						</div>

						{#if isSchoolChangeEditing}
							<div class="enhanced-school-fields grid gap-4 md:grid-cols-2">
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

							<div class="enhanced-school-fields grid gap-4 md:grid-cols-2">
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
						{:else}
							<div class="enhanced-school-fields grid gap-4 md:grid-cols-2">
								<FormField id="state" label="State" required>
									<input
										id="state"
										name="state"
										type="text"
										value={selectedState}
										readonly
										aria-describedby="verified-school-note"
										class={`${inputClass} !bg-slate-100 !text-slate-700`}
									/>
								</FormField>

								<FormField id="county" label="County" required>
									<input
										id="county"
										name="county"
										type="text"
										value={selectedCounty}
										readonly
										aria-describedby="verified-school-note"
										class={`${inputClass} !bg-slate-100 !text-slate-700`}
									/>
								</FormField>
							</div>

							<div class="enhanced-school-fields grid gap-4 md:grid-cols-2">
								<FormField id="district" label="School District" required>
									<input
										id="district"
										name="district"
										type="text"
										value={selectedDistrict}
										readonly
										aria-describedby="verified-school-note"
										class={`${inputClass} !bg-slate-100 !text-slate-700`}
									/>
								</FormField>

								<FormField id="school" label="School" required>
									<input
										id="school"
										name="school"
										type="text"
										value={selectedSchool}
										readonly
										aria-describedby="verified-school-note"
										class={`${inputClass} !bg-slate-100 !text-slate-700`}
									/>
								</FormField>
							</div>
						{/if}
					{:else}
						<div class="enhanced-school-fields grid gap-4 md:grid-cols-2">
							<FormField id="state" label="State" required>
								<select
									id="state"
									name="state"
									required={isEnhanced}
									disabled={!isEnhanced}
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
									required={isEnhanced}
									disabled={!isEnhanced}
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

						<div class="enhanced-school-fields grid gap-4 md:grid-cols-2">
							<FormField id="district" label="School District" required>
								<select
									id="district"
									name="district"
									required={isEnhanced}
									disabled={!isEnhanced}
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
									required={isEnhanced}
									disabled={!isEnhanced}
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
					{/if}

					{#if schoolVerified}
						{#if isSchoolChangeEditing}
							<input type="hidden" name="confirm_school_change" value="true" />
							<div class="flex flex-col gap-3 sm:flex-row">
								<Button
									type="button"
									variant="secondary"
									disabled={isSubmitting}
									onclick={cancelSchoolChange}
									class="w-full"
								>
									Cancel
								</Button>
								<Button type="submit" disabled={isSubmitting} class="w-full">
									Save Updated School
								</Button>
							</div>
						{:else}
							<Button type="button" class="w-full" onclick={startSchoolChange}>
								Update School
							</Button>
						{/if}
					{:else}
						<Button type="submit" disabled={isSubmitting} class="w-full">Update School</Button>
					{/if}
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
					onsubmit={(event) => submitForm(event, '/profile/update_wishlist/', 'Wishlist updated.')}
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
								disabled={!isEnhanced}
								onclick={() => (isWishlistHelpOpen = true)}
							>
								How to Get Link
							</Button>
							<noscript>
								<a
									class="font-semibold text-green-800 underline"
									href={resolve(routes.wishlistSetup)}
								>
									Wishlist setup instructions
								</a>
							</noscript>
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
						<span class="font-mono text-slate-800">www.HelpTeachers.net/teacher/{'{url id}'}</span>
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
