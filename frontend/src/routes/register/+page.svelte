<script lang="ts">
	import { onMount } from 'svelte';
	import { resolve } from '$app/paths';
	import Alert from '$lib/components/Alert.svelte';
	import Button from '$lib/components/Button.svelte';
	import FormField from '$lib/components/FormField.svelte';
	import PageShell from '$lib/components/PageShell.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { apiFetch } from '$lib/api/client';
	import { normalizeStringOptions } from '$lib/api/options';
	import {
		getRecaptchaResponse,
		isRecaptchaMock,
		renderRecaptcha,
		resetRecaptcha
	} from '$lib/recaptcha';
	import { routes } from '$lib/routes';
	import type { ActionData, PageData } from './$types';

	type StatusVariant = 'info' | 'success' | 'warning' | 'error';
	type StatusMessage = { variant: StatusVariant; message: string };
	type ApiMessage = { detail?: string; message?: string };

	let { data, form } = $props<{ data: PageData; form?: ActionData }>();

	const recaptchaSiteKey = '6Lf9uiIqAAAAAMt19WMR4q0aO-JMqks9Du0yHHlL';
	const useMockRecaptcha = isRecaptchaMock();
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
	let termsAccepted = $state(false);
	let mockRecaptchaAccepted = $state(false);
	let isTermsOpen = $state(false);
	let isSubmitting = $state(false);
	let status = $state<StatusMessage | null>(null);
	let schoolOptionsStatus = $state<StatusMessage | null>(null);
	let hasInitializedSchoolOptionsStatus = $state(false);
	let recaptchaContainer = $state<HTMLElement | null>(null);
	let recaptchaWidgetId = $state<number | null>(null);
	let formStatus = $derived(
		form?.message
			? {
					variant: (form.success ? 'success' : 'error') as StatusVariant,
					message: form.message
				}
			: null
	);

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

	onMount(() => {
		let mounted = true;
		if (!useMockRecaptcha && recaptchaContainer) {
			void renderRecaptcha(recaptchaContainer, recaptchaSiteKey)
				.then((widgetId) => {
					if (mounted) {
						recaptchaWidgetId = widgetId;
					}
				})
				.catch((error) => {
					status = {
						variant: 'error',
						message: error instanceof Error ? error.message : 'reCAPTCHA could not be loaded.'
					};
				});
		}

		return () => {
			mounted = false;
			resetRecaptcha(recaptchaWidgetId);
		};
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

	function getSelectValue(event: Event): string {
		const target = event.currentTarget;
		return target instanceof HTMLSelectElement ? target.value : '';
	}

	async function fetchSchoolOptions(path: string): Promise<string[]> {
		const body = await apiFetch<unknown>(path);
		return normalizeStringOptions(body);
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

	async function submitRegistrationForm(event: SubmitEvent) {
		event.preventDefault();

		const form = event.currentTarget;
		if (!(form instanceof HTMLFormElement)) {
			return;
		}

		const formData = new FormData(form);
		const password = String(formData.get('password') ?? '');
		const confirmPassword = String(formData.get('confirm_password') ?? '');
		const recaptchaResponse = getRecaptchaResponse(recaptchaWidgetId, mockRecaptchaAccepted);

		if (password !== confirmPassword) {
			status = {
				variant: 'warning',
				message: 'Passwords do not match. Please ensure both password fields are identical.'
			};
			return;
		}

		if (!termsAccepted) {
			status = {
				variant: 'warning',
				message: 'You must agree to the Terms and Conditions to register.'
			};
			return;
		}

		if (!recaptchaResponse) {
			status = {
				variant: 'warning',
				message: 'Please complete the reCAPTCHA verification.'
			};
			return;
		}

		isSubmitting = true;
		status = { variant: 'info', message: 'Submitting your registration...' };
		formData.append('recaptcha_response', recaptchaResponse);

		try {
			const body = await apiFetch<ApiMessage>('/profile/register/', {
				method: 'POST',
				body: formData
			});
			const message = body.detail || body.message;

			status = {
				variant: 'success',
				message: message || 'Registration successful. Please check your email.'
			};
			form.reset();
			resetCountySelection();
			selectedState = '';
			termsAccepted = false;
		} catch (error) {
			status = {
				variant: 'error',
				message: error instanceof Error ? error.message : 'Registration failed. Please try again.'
			};
		} finally {
			resetRecaptcha(recaptchaWidgetId);
			mockRecaptchaAccepted = false;
			isSubmitting = false;
		}
	}
</script>

<Seo
	title="Homeroom Heroes - Register"
	description="Register as an educator with Homeroom Heroes to create a teacher profile and share your classroom wishlist."
	path={routes.register}
	noindex
/>

<PageShell
	eyebrow="Teacher Sign Up"
	title="User Registration"
	intro="Register as an educator to create your Homeroom Heroes profile and share your classroom wishlist."
>
	<div class="mx-auto max-w-3xl">
		<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
			<div class="space-y-3">
				<h2 class="text-3xl font-bold tracking-normal text-green-800">Teacher Registration</h2>
				<p class="text-base leading-7 text-slate-700">
					Please fill out the form below. If your school is not present in the list, visit the
					<a
						href={resolve(routes.contact)}
						class="font-semibold text-green-700 hover:text-green-900 hover:underline"
					>
						Contact page
					</a>
					and send us a message.
				</p>
			</div>

			{#if schoolOptionsStatus}
				<div class="mt-5">
					<Alert variant={schoolOptionsStatus.variant}>{schoolOptionsStatus.message}</Alert>
				</div>
			{/if}

			<form
				action={routes.register}
				method="post"
				enctype="multipart/form-data"
				class="mt-7 space-y-5"
				onsubmit={submitRegistrationForm}
			>
				<div class="grid gap-5 md:grid-cols-2">
					<FormField id="name" label="Name" required>
						<input id="name" name="name" type="text" required class={inputClass} />
					</FormField>

					<FormField id="email" label="Email" required>
						<input id="email" name="email" type="email" required class={inputClass} />
					</FormField>
				</div>

				<FormField id="phone_number" label="Phone Number" required>
					<input id="phone_number" name="phone_number" type="tel" required class={inputClass} />
				</FormField>

				<div class="grid gap-5 md:grid-cols-2">
					<FormField id="password" label="Password" required>
						<input id="password" name="password" type="password" required class={inputClass} />
					</FormField>

					<FormField id="confirm_password" label="Confirm Password" required>
						<input
							id="confirm_password"
							name="confirm_password"
							type="password"
							required
							class={inputClass}
						/>
					</FormField>
				</div>

				<div class="grid gap-5 md:grid-cols-2">
					<FormField id="state" label="State" required>
						<select
							id="state"
							name="state"
							required
							bind:value={selectedState}
							onchange={handleStateChange}
							class={inputClass}
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
							disabled={!selectedState}
							bind:value={selectedCounty}
							onchange={handleCountyChange}
							class={inputClass}
						>
							<option value="" disabled>Choose county</option>
							{#each counties as county (county)}
								<option value={county}>{county}</option>
							{/each}
						</select>
					</FormField>
				</div>

				<div class="grid gap-5 md:grid-cols-2">
					<FormField id="district" label="School District" required>
						<select
							id="district"
							name="district"
							required
							disabled={!selectedCounty}
							bind:value={selectedDistrict}
							onchange={handleDistrictChange}
							class={inputClass}
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
							disabled={!selectedDistrict}
							bind:value={selectedSchool}
							class={inputClass}
						>
							<option value="" disabled>Choose school</option>
							{#each schools as school (school)}
								<option value={school}>{school}</option>
							{/each}
						</select>
					</FormField>
				</div>

				<div class="rounded-lg border border-slate-200 bg-slate-50 p-5">
					<div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
						<div>
							<h3 class="text-lg font-bold tracking-normal text-slate-950">Terms and Conditions</h3>
							<p class="mt-1 text-sm leading-6 text-slate-600">
								Review the terms before submitting your registration.
							</p>
						</div>
						<Button type="button" variant="secondary" onclick={() => (isTermsOpen = true)}>
							Open Terms
						</Button>
					</div>

					<label
						class="mt-4 flex items-start gap-3 text-sm leading-6 text-slate-700"
						for="termsCheckbox"
					>
						<input
							id="termsCheckbox"
							name="termsCheckbox"
							type="checkbox"
							required
							bind:checked={termsAccepted}
							class="mt-1 size-4 rounded border-slate-300 text-green-700 focus:outline-2 focus:outline-green-600"
						/>
						<span>I have read the Terms and Conditions</span>
					</label>
				</div>

				<div class="min-h-20">
					{#if useMockRecaptcha}
						<div class="rounded-md border border-blue-200 bg-blue-50 p-4 text-blue-950">
							<label class="flex items-center gap-3 font-semibold" for="recaptcha-mock">
								<input
									id="recaptcha-mock"
									type="checkbox"
									bind:checked={mockRecaptchaAccepted}
									class="size-5 rounded border-slate-300 text-green-700 focus:outline-2 focus:outline-green-600"
								/>
								<span>I'm not a robot (local test CAPTCHA)</span>
							</label>
							<p class="mt-2 text-sm">This mock is enabled only for local manual testing.</p>
						</div>
					{:else}
						<div
							bind:this={recaptchaContainer}
							class="g-recaptcha"
							data-sitekey={recaptchaSiteKey}
						></div>
					{/if}
				</div>

				<div class="flex flex-col gap-3 sm:flex-row">
					<Button type="submit" disabled={isSubmitting} class="w-full">
						{isSubmitting ? 'Submitting...' : 'Submit'}
					</Button>
					<Button href={routes.login} variant="secondary" class="w-full">Login</Button>
				</div>
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

{#if isTermsOpen}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/65 p-4">
		<div
			role="dialog"
			aria-modal="true"
			aria-labelledby="terms-dialog-title"
			class="max-h-full w-full max-w-4xl overflow-hidden rounded-lg bg-white shadow-xl"
		>
			<div class="flex items-center justify-between border-b border-slate-200 px-5 py-4">
				<h2 id="terms-dialog-title" class="text-xl font-bold tracking-normal text-slate-950">
					Terms and Conditions
				</h2>
				<button
					type="button"
					class="rounded-md px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-green-700"
					onclick={() => (isTermsOpen = false)}
				>
					Close
				</button>
			</div>
			<iframe src={routes.terms} title="Terms and Conditions" class="h-[70vh] w-full"></iframe>
		</div>
	</div>
{/if}
