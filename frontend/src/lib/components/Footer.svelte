<script lang="ts">
	import { resolve } from '$app/paths';
	import { routes } from '$lib/routes';

	const footerLinks = [
		{ label: 'About', href: routes.about },
		{ label: 'Contact', href: routes.contact },
		{ label: 'Partners', href: routes.partners },
		{ label: 'Terms', href: routes.terms },
		{ label: 'Wishlist Setup', href: routes.wishlistSetup }
	];

	const year = new Date().getFullYear();
</script>

<footer class="border-t border-slate-200 bg-slate-950 text-slate-200">
	<div
		class="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-8 sm:px-6 md:flex-row md:items-center md:justify-between lg:px-8"
	>
		<div>
			<a
				href={resolve(routes.home)}
				class="inline-flex rounded-md focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-white"
			>
				<img
					src="/images/logo_transparent.png"
					alt="Homeroom Heroes"
					width="298"
					height="95"
					class="h-10 w-auto"
				/>
			</a>
			<p class="mt-3 text-sm text-slate-400">
				Copyright {year} Homeroom Heroes. All rights reserved.
			</p>
		</div>

		<nav aria-label="Footer" class="flex flex-wrap gap-x-5 gap-y-2 text-sm font-medium">
			{#each footerLinks as item (item.href)}
				<a href={resolve(item.href as '/')} class="text-slate-300 transition hover:text-white">
					{item.label}
				</a>
			{/each}
		</nav>
	</div>
</footer>
