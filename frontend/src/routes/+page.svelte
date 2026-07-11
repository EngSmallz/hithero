<script lang="ts">
	import { onMount } from 'svelte';
	import Button from '$lib/components/Button.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { getBackendOrigin } from '$lib/api/client';
	import { routes } from '$lib/routes';

	type FeaturedTeacher = {
		name?: string | null;
		state?: string | null;
		county?: string | null;
		school?: string | null;
		image_data?: string | null;
	};

	type Promo = {
		promo_image_url?: string | null;
		promo_title?: string | null;
	};

	const backendOrigin = getBackendOrigin();

	const metrics = [
		{
			label: 'Verified teachers',
			value: '150+',
			description: 'Educators with active profiles ready for support',
			accent: 'bg-green-300'
		},
		{
			label: 'Total donations',
			value: '$9.3k',
			description: 'Raised by generous donors for classroom supplies',
			accent: 'bg-amber-300'
		},
		{
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

	let spotlight = $state<FeaturedTeacher | null>(null);
	let randomTeacher = $state<FeaturedTeacher | null>(null);
	let promo = $state<Promo | null>(null);
	let spotlightError = $state('');
	let randomTeacherError = $state('');
	let isLoadingRandomTeacher = $state(false);

	onMount(() => {
		void Promise.all([loadSpotlight(), loadPromo()]);
	});

	async function loadSpotlight() {
		try {
			const response = await fetch(`${backendOrigin}/spotlight/teacher`, {
				credentials: 'include'
			});
			if (!response.ok) {
				throw new Error('Teacher of the Day is temporarily unavailable.');
			}
			spotlight = (await response.json()) as FeaturedTeacher;
			spotlightError = '';
		} catch (error) {
			spotlightError =
				error instanceof Error ? error.message : 'Teacher of the Day is temporarily unavailable.';
		}
	}

	async function loadPromo() {
		try {
			const response = await fetch(`${backendOrigin}/promo/get_promo_info/`, {
				credentials: 'include'
			});
			if (!response.ok) return;
			const loadedPromo = (await response.json()) as Promo;
			promo = loadedPromo.promo_image_url ? loadedPromo : null;
		} catch {
			promo = null;
		}
	}

	async function findRandomTeacher() {
		isLoadingRandomTeacher = true;
		randomTeacherError = '';
		try {
			const response = await fetch(`${backendOrigin}/api/random_teacher/`, {
				credentials: 'include'
			});
			if (!response.ok) {
				throw new Error('A random teacher could not be selected. Please try again.');
			}
			randomTeacher = (await response.json()) as FeaturedTeacher;
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
</script>

<Seo
	title="Homeroom Heroes - Support Teachers"
	description="Connect with teachers who need classroom supplies and help Homeroom Heroes support students nationwide."
	path={routes.home}
/>

<div class="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
	<section
		class="relative overflow-hidden rounded-lg bg-cover bg-center shadow-lg"
		style="background-image: url('/images/homepage/hero_border.jpg');"
	>
		<div class="absolute inset-0 bg-slate-950/65"></div>
		<div
			class="relative z-10 flex min-h-[28rem] flex-col items-center justify-center px-6 py-16 text-center text-white"
		>
			<p class="text-sm font-semibold uppercase tracking-wide text-green-200">Homeroom Heroes</p>
			<h1 class="mt-4 max-w-4xl text-4xl font-extrabold tracking-normal sm:text-6xl">
				Support Teachers, Empower Futures!
			</h1>
			<p class="mt-5 max-w-2xl text-xl leading-8 text-slate-100">
				Connecting generous donors with teachers in need of classroom supplies.
			</p>
			<div class="mt-8 flex flex-wrap justify-center gap-3">
				<Button href={routes.teachers} size="lg">Find Teachers to Support</Button>
				<Button href={routes.register} variant="secondary" size="lg">Register as a Teacher</Button>
			</div>
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
	{/if}

	<section
		class="mt-8 rounded-lg bg-gradient-to-r from-green-800 to-green-950 px-6 py-8 text-white shadow-lg"
	>
		<div class="mb-6 text-center">
			<p class="text-xs font-semibold uppercase tracking-widest text-green-300">
				Our impact so far
			</p>
			<h2 class="mt-2 text-2xl font-bold tracking-normal">
				Every number is a classroom transformed
			</h2>
		</div>

		<div class="grid gap-4 md:grid-cols-3">
			{#each metrics as metric (metric.label)}
				<article class="rounded-lg border border-white/15 bg-white/10 p-5">
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

	<section class="mt-8 grid gap-6 md:grid-cols-2">
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
					<Button href={routes.teacher} class="mt-6">View Teacher of the Day</Button>
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
						<Button href={routes.teacher} variant="secondary" class="mt-4">
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
