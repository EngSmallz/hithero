<script lang="ts">
	import Button from '$lib/components/Button.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { routes } from '$lib/routes';

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
			title: 'Teacher of the Day',
			description: 'Meet educators who are making a daily difference for students.',
			image: '/images/homepage/tile_border_1.jpg',
			href: routes.teachers,
			label: 'Browse Teachers'
		},
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
		},
		{
			title: 'Find a Random Teacher',
			description: 'Start browsing and discover a teacher whose classroom you can support.',
			image: '/images/homepage/tile_border_2.jpg',
			href: routes.teachers,
			label: 'Find Teachers'
		}
	];
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
	</section>
</div>
