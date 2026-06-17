<script lang="ts">
	import { resolve } from '$app/paths';
	import PageShell from '$lib/components/PageShell.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { routes } from '$lib/routes';

	const partnerGroups = [
		{
			title: 'Radio Partners',
			partners: [
				{
					name: '100.7 The Wolf Seattle - Morning Wolf Pack with Matt McAllister, Gabe, and Ron',
					href: 'https://www.seattlewolf.com',
					image: '/images/partners/1007TheWolf.png',
					alt: '100.7 The Wolf Seattle logo'
				},
				{
					name: '96.5 Live Free Country - Michael in the Afternoon',
					href: 'https://www.livefreecountry.com',
					image: '/images/partners/965CountryColor.png',
					alt: '96.5 Live Free Country logo'
				}
			]
		},
		{
			title: 'Event Partners',
			partners: [
				{
					name: 'Base Camp Studio - Seattle, WA',
					href: 'https://www.basecamp206.com/',
					image: '/images/partners/BaseCamp.png',
					alt: 'Base Camp Studio logo'
				}
			]
		},
		{
			title: 'Financial Partners',
			partners: [
				{
					name: 'Coastal Community Bank - Darrington, WA',
					href: 'https://www.coastalbank.com/darrington/',
					image: '/images/partners/Coastal.png',
					alt: 'Coastal Community Bank logo'
				}
			]
		}
	];
</script>

<Seo
	title="Homeroom Heroes - Sponsors and Thank You"
	description="Thank you to the radio, event, and financial partners supporting Homeroom Heroes classrooms."
	path={routes.partners}
/>

<PageShell
	eyebrow="Partners"
	title="Thank You to Our Partners"
	intro="We are thankful for the partners whose support helps us make a lasting impact for teachers and students."
>
	<div class="space-y-8">
		<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
			<p class="text-lg leading-8 text-slate-700">
				Your contributions have made a lasting impact on the lives of teachers and students, helping
				us grow into the organization we are today. Together, we are making a meaningful difference
				in classrooms across the country.
			</p>
		</section>

		{#each partnerGroups as group (group.title)}
			<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
				<h2 class="text-center text-2xl font-bold tracking-normal text-green-800">
					{group.title}
				</h2>
				<div class="mt-6 grid gap-6 md:grid-cols-3">
					{#each group.partners as partner (partner.name)}
						<article class="rounded-lg border border-slate-200 bg-slate-50 p-5 text-center">
							<h3 class="text-lg font-bold tracking-normal text-slate-950">{partner.name}</h3>
							<!-- eslint-disable svelte/no-navigation-without-resolve -->
							<a
								href={partner.href}
								target="_blank"
								rel="noreferrer"
								class="mt-5 block rounded-md bg-white p-4 ring-1 ring-slate-200 transition hover:ring-green-300"
							>
								<img
									src={partner.image}
									alt={partner.alt}
									width="220"
									height="120"
									class="mx-auto h-24 w-full object-contain"
									loading="lazy"
								/>
							</a>
							<!-- eslint-enable svelte/no-navigation-without-resolve -->
							<p class="mt-3 text-sm text-slate-600">Visit their website for more info.</p>
						</article>
					{/each}
				</div>
			</section>
		{/each}

		<section
			class="rounded-lg border border-green-200 bg-green-50 p-6 text-center shadow-sm sm:p-8"
		>
			<h2 class="text-2xl font-bold tracking-normal text-green-900">Become a Partner</h2>
			<p class="mx-auto mt-3 max-w-2xl text-lg leading-8 text-green-950">
				If you are interested in becoming a partner, fill out the form on the
				<a
					href={resolve(routes.contact as '/')}
					class="font-semibold text-green-800 underline hover:text-green-950"
				>
					Contact page
				</a>
				or reach out on social media. Becoming a partner is easy and can make a difference in your community.
			</p>
		</section>
	</div>
</PageShell>
