<script lang="ts">
	import { untrack } from 'svelte';
	import Button from '$lib/components/Button.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { apiFetch, getBackendOrigin } from '$lib/api/client';
	import { routes } from '$lib/routes';
	import type { PageData } from './$types';

	type FeaturedTeacher = {
		name?: string | null;
		state?: string | null;
		county?: string | null;
		school?: string | null;
		image_data?: string | null;
		url_id?: string | null;
	};

	type Promo = {
		promo_image_url?: string | null;
		promo_title?: string | null;
	};

	const backendOrigin = getBackendOrigin();
	let { data } = $props<{ data: PageData }>();

	const metrics = [
		{
			icon: 'teacher',
			iconBackground: 'bg-green-300/20',
			iconColor: 'text-green-300',
			label: 'Verified teachers',
			value: '150+',
			description: 'Educators with active profiles ready for support',
			accent: 'bg-green-300'
		},
		{
			icon: 'donations',
			iconBackground: 'bg-amber-300/20',
			iconColor: 'text-amber-300',
			label: 'Total donations',
			value: '$9.3k',
			description: 'Raised by generous donors for classroom supplies',
			accent: 'bg-amber-300'
		},
		{
			icon: 'schools',
			iconBackground: 'bg-violet-300/20',
			iconColor: 'text-violet-300',
			label: 'Schools reached',
			value: '135+',
			description: 'Schools with at least one supported teacher',
			accent: 'bg-violet-300'
		}
	];

	const actionCards = [
		{
			title: 'Are You a Teacher?',
			description: 'Register to create your profile and share your classroom needs.',
			image: '/images/homepage/tile_border_3.jpg',
			href: routes.register,
			label: 'Register'
		},
		{
			title: 'Donate Directly to Us',
			description: 'Make a direct contribution to Homeroom Heroes operations and programs.',
			image: '/images/homepage/tile_border_4.jpg',
			externalHref: 'https://www.paypal.com/donate/?hosted_button_id=B8NRR79ZEV2PS',
			label: 'Donate'
		}
	];

	const initialData = untrack(() => data);
	let spotlight = $state<FeaturedTeacher | null>(initialData.spotlight);
	let randomTeacher = $state<FeaturedTeacher | null>(initialData.randomTeacher);
	let promo = $state<Promo | null>(initialData.promo);
	let spotlightError = $state(
		initialData.spotlightUnavailable ? 'Teacher of the Day is temporarily unavailable.' : ''
	);
	let promoError = $state(
		initialData.promoUnavailable ? 'Promotion information is temporarily unavailable.' : ''
	);
	let randomTeacherError = $state(
		initialData.randomTeacherUnavailable ? 'A random teacher could not be selected.' : ''
	);
	let isLoadingRandomTeacher = $state(false);

	async function findRandomTeacher() {
		isLoadingRandomTeacher = true;
		randomTeacherError = '';
		try {
			randomTeacher = await apiFetch<FeaturedTeacher>('/api/random_teacher/');
		} catch (error) {
			randomTeacher = null;
			randomTeacherError =
				error instanceof Error ? error.message : 'A random teacher could not be selected.';
		} finally {
			isLoadingRandomTeacher = false;
		}
	}

	function teacherImage(teacher: FeaturedTeacher): string {
		return teacher.image_data
			? `data:image/jpeg;base64,${teacher.image_data}`
			: new URL('/static/images/apple.jpg', backendOrigin).toString();
	}

	function promoImageUrl(value: string): string {
		return /^https?:\/\//.test(value) ? value : new URL(value, backendOrigin).toString();
	}

	function teacherHref(teacher: FeaturedTeacher): string {
		return teacher.url_id ? `/teacher/${encodeURIComponent(teacher.url_id)}` : routes.teachers;
	}
</script>

<Seo
	title="Homeroom Heroes - Support Teachers"
	description="Connect with teachers who need classroom supplies and help Homeroom Heroes support students nationwide."
	path={routes.home}
/>

<div class="min-h-full bg-gray-800 px-4 py-8 text-gray-50 sm:px-6 lg:px-8">
	<div class="mx-auto w-full max-w-[1730px]">
		<section
			class="relative overflow-hidden rounded-lg bg-cover bg-center shadow-lg"
			style="background-image: url('/images/homepage/hero_border.jpg');"
		>
			<div class="absolute inset-0 bg-slate-950/65"></div>
			<div
				class="relative z-10 flex min-h-[24rem] flex-col items-center justify-center px-6 py-12 text-center text-white"
			>
				<h1 class="text-4xl font-extrabold tracking-normal sm:text-6xl">
					Support Teachers, Empower Futures!
				</h1>
				<p class="mt-5 text-xl font-light leading-8 text-slate-100 md:text-2xl">
					Connecting generous donors with teachers in need of classroom supplies.
				</p>
				<Button href={routes.teachers} size="lg" class="mt-8">Find Teachers to Support</Button>
			</div>
		</section>

	{#if promo?.promo_image_url}
		<section
			class="mt-8 overflow-hidden rounded-lg border-4 border-green-600 bg-green-950 p-6 text-center text-white shadow-lg"
			aria-label="Special promotion"
		>
			<img
				src={promoImageUrl(promo.promo_image_url)}
				alt={promo.promo_title || 'Homeroom Heroes promotion'}
				class="mx-auto max-h-96 w-auto rounded-md object-contain"
			/>
			<h2 class="mt-5 text-3xl font-bold tracking-normal">
				{promo.promo_title || 'Special Promotion!'}
			</h2>
		</section>
	{:else if promoError}
		<p class="mt-8 rounded-md border border-red-200 bg-red-50 p-4 text-red-950" role="alert">
			{promoError}
		</p>
	{/if}

	<section
		class="mt-8 rounded-lg bg-gradient-to-r from-green-800 to-green-900 px-6 py-8 text-white shadow-lg"
	>
		<div class="mb-6 text-center">
			<p class="text-xs font-semibold uppercase tracking-widest text-green-300">
				Our impact so far
			</p>
			<h2 class="mt-2 font-serif text-xl font-medium tracking-normal sm:text-2xl">
				Every number is a classroom transformed
			</h2>
		</div>

		<div class="grid gap-4 md:grid-cols-3">
			{#each metrics as metric (metric.label)}
				<article class="rounded-lg border border-white/15 bg-white/10 p-5">
					<div
						class={`mb-4 flex size-9 items-center justify-center rounded-full ${metric.iconBackground} ${metric.iconColor}`}
					>
						{#if metric.icon === 'teacher'}
							<svg
								aria-hidden="true"
								width="18"
								height="18"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
							>
								<path d="M22 10v6M2 10l10-5 10 5-10 5z" />
								<path d="M6 12v5c3 3 9 3 12 0v-5" />
							</svg>
						{:else if metric.icon === 'donations'}
							<svg
								aria-hidden="true"
								width="18"
								height="18"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
							>
								<line x1="12" y1="1" x2="12" y2="23" />
								<path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" />
							</svg>
						{:else}
							<svg
								aria-hidden="true"
								width="18"
								height="18"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
							>
								<path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
								<polyline points="9 22 9 12 15 12 15 22" />
							</svg>
						{/if}
					</div>
					<p class="text-xs font-semibold uppercase tracking-widest text-green-200">
						{metric.label}
					</p>
					<p class="mt-3 text-4xl font-bold tracking-normal">{metric.value}</p>
					<div class={`my-4 h-1 w-10 rounded-full ${metric.accent}`}></div>
					<p class="text-sm leading-6 text-green-100">{metric.description}</p>
				</article>
			{/each}
		</div>
	</section>

	<section class="mt-8 grid gap-8 md:grid-cols-2">
		<article
			class="relative min-h-72 overflow-hidden rounded-lg bg-cover bg-center shadow-md"
			style="background-image: url('/images/homepage/tile_border_1.jpg');"
		>
			<div class="absolute inset-0 bg-slate-950/65"></div>
			<div
				class="relative z-10 flex h-full min-h-72 flex-col items-center justify-center p-8 text-center text-white"
			>
				<h2 class="text-3xl font-bold tracking-normal">Teacher of the Day</h2>
				{#if spotlight}
					<img
						src={teacherImage(spotlight)}
						alt={`${spotlight.name || 'Featured teacher'} profile`}
						class="mt-5 size-36 rounded-full border-2 border-green-300 object-cover"
					/>
					<p class="mt-4 text-2xl font-semibold">{spotlight.name || 'Featured Teacher'}</p>
					<p class="mt-1 text-base text-slate-100">
						{spotlight.school || 'School unavailable'} in
						{[spotlight.county, spotlight.state].filter(Boolean).join(', ')}
					</p>
					<Button href={teacherHref(spotlight)} class="mt-6">View Teacher of the Day</Button>
				{:else if spotlightError}
					<p class="mt-4 max-w-md text-red-100">{spotlightError}</p>
					<Button href={routes.teachers} variant="secondary" class="mt-6">Browse Teachers</Button>
				{:else}
					<p class="mt-4 text-slate-100">Loading teacher of the day...</p>
				{/if}
			</div>
		</article>

		{#each actionCards as card (card.title)}
			<article
				class="relative min-h-72 overflow-hidden rounded-lg bg-cover bg-center shadow-md"
				style={`background-image: url('${card.image}');`}
			>
				<div class="absolute inset-0 bg-slate-950/65"></div>
				<div
					class="relative z-10 flex h-full min-h-72 flex-col items-center justify-center p-8 text-center text-white"
				>
					<h2 class="text-3xl font-bold tracking-normal">{card.title}</h2>
					<p class="mt-4 max-w-md text-lg leading-7 text-slate-100">{card.description}</p>
					{#if card.href}
						<Button href={card.href} class="mt-6">{card.label}</Button>
					{:else if card.externalHref}
						<!-- eslint-disable svelte/no-navigation-without-resolve -->
						<a
							href={card.externalHref}
							target="_blank"
							rel="noreferrer"
							class="mt-6 inline-flex min-h-11 items-center justify-center rounded-md bg-green-700 px-4 text-base font-semibold text-white shadow-sm transition hover:bg-green-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-200"
						>
							{card.label}
						</a>
						<!-- eslint-enable svelte/no-navigation-without-resolve -->
					{/if}
				</div>
			</article>
		{/each}

		<article
			class="relative min-h-72 overflow-hidden rounded-lg bg-cover bg-center shadow-md"
			style="background-image: url('/images/homepage/tile_border_2.jpg');"
		>
			<div class="absolute inset-0 bg-slate-950/65"></div>
			<div
				class="relative z-10 flex h-full min-h-72 flex-col items-center justify-center p-8 text-center text-white"
			>
				<h2 class="text-3xl font-bold tracking-normal">Find a Random Teacher</h2>
				<p class="mt-4 max-w-md text-lg leading-7 text-slate-100">
					Discover a teacher at random and make a positive impact on their classroom.
				</p>
				<Button
					type="button"
					class="mt-6"
					disabled={isLoadingRandomTeacher}
					onclick={() => void findRandomTeacher()}
				>
					{isLoadingRandomTeacher ? 'Finding a Teacher...' : 'Find Random Teacher'}
				</Button>

				{#if randomTeacher}
					<div class="mt-6 flex flex-col items-center">
						<img
							src={teacherImage(randomTeacher)}
							alt={`${randomTeacher.name || 'Random teacher'} profile`}
							class="size-36 rounded-full border-2 border-green-300 object-cover"
						/>
						<p class="mt-4 text-2xl font-semibold">{randomTeacher.name || 'Teacher'}</p>
						<p class="mt-1 text-base text-slate-100">
							{randomTeacher.school || 'School unavailable'} in
							{[randomTeacher.county, randomTeacher.state].filter(Boolean).join(', ')}
						</p>
						<Button href={teacherHref(randomTeacher)} variant="secondary" class="mt-4">
							View Random Teacher
						</Button>
					</div>
				{:else if randomTeacherError}
					<p class="mt-4 text-red-100" role="alert">{randomTeacherError}</p>
				{/if}
			</div>
		</article>
	</section>
	</div>
</div>
