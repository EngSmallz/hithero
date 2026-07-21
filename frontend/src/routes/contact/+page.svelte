<script lang="ts">
	import { onMount } from 'svelte';
	import Alert from '$lib/components/Alert.svelte';
	import Button from '$lib/components/Button.svelte';
	import FormField from '$lib/components/FormField.svelte';
	import PageShell from '$lib/components/PageShell.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { apiFetch } from '$lib/api/client';
	import {
		getRecaptchaResponse,
		isRecaptchaMock,
		renderRecaptcha,
		resetRecaptcha
	} from '$lib/recaptcha';
	import { routes } from '$lib/routes';
	import type { ActionData } from './$types';

	type StatusVariant = 'info' | 'success' | 'warning' | 'error';

	const recaptchaSiteKey = '6Lf9uiIqAAAAAMt19WMR4q0aO-JMqks9Du0yHHlL';
	const useMockRecaptcha = isRecaptchaMock();
	const socialLinks = [
		{
			label: 'Instagram',
			value: '@Homeroom_Heroes',
			href: 'https://www.instagram.com/homeroom_heroes/'
		},
		{ label: 'X', value: '@Homeroom_Heroes', href: 'https://www.x.com/Homeroom_Heroes' },
		{
			label: 'LinkedIn',
			value: 'Homeroom Heroes',
			href: 'https://www.linkedin.com/company/homeroom-heroes/'
		},
		{
			label: 'Facebook',
			value: 'Homeroom Heroes',
			href: 'https://www.facebook.com/profile.php?id=61557539257533'
		},
		{
			label: 'Threads',
			value: '@Homeroom_Heroes',
			href: 'https://www.threads.com/@homeroom_heroes'
		}
	];

	let message = $state('');
	let isSubmitting = $state(false);
	let status = $state<{ variant: StatusVariant; message: string } | null>(null);
	let charactersRemaining = $derived(250 - message.length);
	let recaptchaContainer = $state<HTMLElement | null>(null);
	let recaptchaWidgetId = $state<number | null>(null);
	let mockRecaptchaAccepted = $state(false);
	let { form } = $props<{ form?: ActionData }>();
	let formStatus = $derived(
		form?.message
			? {
					variant: (form.success ? 'success' : 'error') as StatusVariant,
					message: form.message
				}
			: null
	);

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

	async function submitContactForm(event: SubmitEvent) {
		event.preventDefault();

		const form = event.currentTarget;
		if (!(form instanceof HTMLFormElement)) {
			return;
		}

		const recaptchaResponse = getRecaptchaResponse(recaptchaWidgetId, mockRecaptchaAccepted);

		if (!recaptchaResponse) {
			status = {
				variant: 'warning',
				message: 'Please complete the reCAPTCHA to send your message.'
			};
			return;
		}

		isSubmitting = true;
		status = { variant: 'info', message: 'Sending your message...' };

		const formData = new FormData(form);
		formData.append('recaptcha_response', recaptchaResponse);

		try {
			const body = await apiFetch<{ message?: string; detail?: string }>('/api/contact_us/', {
				method: 'POST',
				body: formData
			});

			form.reset();
			message = '';
			status = {
				variant: 'success',
				message: body.message || 'Message sent successfully.'
			};
		} catch (error) {
			status = {
				variant: 'error',
				message: error instanceof Error ? error.message : 'An error occurred. Please try again.'
			};
		} finally {
			resetRecaptcha(recaptchaWidgetId);
			mockRecaptchaAccepted = false;
			isSubmitting = false;
		}
	}
</script>

<Seo
	title="Homeroom Heroes - Contact Us"
	description="Contact Homeroom Heroes with questions, feedback, partnership inquiries, or support needs."
	path={routes.contact}
/>

<PageShell
	eyebrow="Contact"
	title="Contact Us"
	intro="Reach out to Homeroom Heroes with questions, feedback, partnership ideas, or support needs."
>
	<div class="grid gap-8 lg:grid-cols-[0.85fr_1.15fr]">
		<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
			<h2 class="text-3xl font-bold tracking-normal text-green-800">Contact Information</h2>
			<p class="mt-4 text-base leading-7 text-slate-700">
				If you have any questions, feedback, or need assistance, please reach out through one of our
				social channels.
			</p>

			<ul class="mt-6 space-y-3">
				{#each socialLinks as link (link.label)}
					<li class="rounded-md border border-slate-200 bg-slate-50 p-4">
						<p class="text-sm font-semibold uppercase tracking-wide text-slate-500">
							{link.label}
						</p>
						<!-- eslint-disable svelte/no-navigation-without-resolve -->
						<a
							href={link.href}
							target="_blank"
							rel="noreferrer"
							class="mt-1 inline-block font-semibold text-green-700 hover:text-green-900 hover:underline"
						>
							{link.value}
						</a>
						<!-- eslint-enable svelte/no-navigation-without-resolve -->
					</li>
				{/each}
			</ul>
		</section>

		<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
			<h2 class="text-3xl font-bold tracking-normal text-green-800">Contact Form</h2>
			<p class="mt-4 text-base leading-7 text-slate-700">
				You can also send us a message using the contact form below.
			</p>

			<form
				action={routes.contact}
				method="post"
				enctype="multipart/form-data"
				class="mt-6 space-y-5"
				onsubmit={submitContactForm}
			>
				<FormField id="name" label="Name" required>
					<input
						id="name"
						name="name"
						type="text"
						required
						class="block min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-950 shadow-sm focus:border-green-600 focus:outline-2 focus:outline-green-600"
					/>
				</FormField>

				<FormField id="email" label="Email" required>
					<input
						id="email"
						name="email"
						type="email"
						required
						class="block min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-950 shadow-sm focus:border-green-600 focus:outline-2 focus:outline-green-600"
					/>
				</FormField>

				<FormField id="subject" label="Subject" required>
					<input
						id="subject"
						name="subject"
						type="text"
						required
						class="block min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-950 shadow-sm focus:border-green-600 focus:outline-2 focus:outline-green-600"
					/>
				</FormField>

				<FormField
					id="message"
					label="Message"
					help={`${charactersRemaining} characters remaining`}
					required
				>
					<textarea
						id="message"
						name="message"
						maxlength="250"
						rows="5"
						required
						bind:value={message}
						class="block w-full resize-y rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-950 shadow-sm focus:border-green-600 focus:outline-2 focus:outline-green-600"
					></textarea>
				</FormField>

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

				<Button type="submit" disabled={isSubmitting} class="w-full">
					{isSubmitting ? 'Sending...' : 'Submit'}
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
