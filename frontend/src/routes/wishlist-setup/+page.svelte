<script lang="ts">
	import PageShell from '$lib/components/PageShell.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { routes } from '$lib/routes';

	const steps = [
		{
			title: 'Go to Amazon.com.',
			href: 'https://www.amazon.com'
		},
		{
			title: 'Go to "Accounts & Lists".',
			image: '/images/wishlist/amazon1.JPG',
			alt: 'Amazon Accounts and Lists menu'
		},
		{
			title: 'Go to "Your Lists".',
			image: '/images/wishlist/amazon2.JPG',
			alt: 'Amazon Your Lists menu'
		},
		{
			title: 'Create a list.',
			image: '/images/wishlist/amazon3.JPG',
			alt: 'Amazon create list option'
		},
		{
			title: 'Name your list and save it.',
			image: '/images/wishlist/amazon4.JPG',
			alt: 'Amazon list naming dialog'
		},
		{
			title: 'Add items to your list that you need for your classroom.'
		},
		{
			title: 'Go to your list, hover over the "More" button, then click "Manage List".',
			image: '/images/wishlist/amazon5.JPG',
			alt: 'Amazon Manage List option'
		},
		{
			title:
				'In "Manage List," set privacy to "Shared" and choose your preferred shipping address. Do not share your shipping address publicly.',
			image: '/images/wishlist/amazon6.JPG',
			alt: 'Amazon Manage List settings'
		},
		{
			title: 'Click "Send list to others".',
			image: '/images/wishlist/amazon7.JPG',
			alt: 'Amazon Send list to others option'
		},
		{
			title: 'Click "View only" and then "Copy link".',
			image: '/images/wishlist/amazon8.JPG',
			alt: 'Amazon Copy link option'
		}
	];
</script>

<Seo
	title="Steps to Setup Wishlist - Homeroom Heroes"
	description="Follow step-by-step instructions for creating and sharing an Amazon classroom wishlist with Homeroom Heroes."
	path={routes.wishlistSetup}
	noindex
/>

<PageShell
	eyebrow="Teacher Resources"
	title="Steps to Setup Wishlist"
	intro="Use these steps to create a shareable Amazon wishlist for your classroom supplies."
	narrow
>
	<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
		<ol class="space-y-8">
			{#each steps as step, index (step.title)}
				<li
					class="grid gap-5 border-b border-slate-200 pb-8 last:border-b-0 last:pb-0 sm:grid-cols-[3rem_1fr]"
				>
					<div
						class="flex size-11 items-center justify-center rounded-full bg-green-100 text-lg font-bold text-green-800"
					>
						{index + 1}
					</div>
					<div>
						<p class="text-xl font-semibold leading-8 text-slate-950">
							{#if step.href}
								<!-- eslint-disable svelte/no-navigation-without-resolve -->
								<a
									href={step.href}
									target="_blank"
									rel="noreferrer"
									class="text-green-700 underline hover:text-green-900"
								>
									{step.title}
								</a>
								<!-- eslint-enable svelte/no-navigation-without-resolve -->
							{:else}
								{step.title}
							{/if}
						</p>
						{#if step.image && step.alt}
							<img
								src={step.image}
								alt={step.alt}
								width="900"
								height="600"
								class="mt-4 w-full rounded-lg border border-slate-200 shadow-sm"
								loading="lazy"
							/>
						{/if}
					</div>
				</li>
			{/each}
		</ol>
	</section>
</PageShell>
