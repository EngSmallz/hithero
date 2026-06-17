<script lang="ts">
	import { resolve } from '$app/paths';
	import { publicNavItems, routes } from '$lib/routes';

	let { currentPath = routes.home } = $props<{
		currentPath?: string;
	}>();

	let isMenuOpen = $state(false);

	function closeMenu() {
		isMenuOpen = false;
	}

	function isActive(href: string): boolean {
		return href === routes.home ? currentPath === routes.home : currentPath.startsWith(href);
	}

	function navLinkClass(href: string): string {
		const activeClass = isActive(href)
			? 'bg-white/15 text-white'
			: 'text-green-50 hover:bg-white/10 hover:text-white';

		return `rounded-md px-3 py-2 text-sm font-semibold transition ${activeClass}`;
	}

	function mobileLinkClass(href: string): string {
		const activeClass = isActive(href)
			? 'bg-green-700 text-white'
			: 'text-green-950 hover:bg-green-50';

		return `block rounded-md px-3 py-2 text-base font-semibold transition ${activeClass}`;
	}
</script>

<header class="bg-green-800 text-white shadow-sm">
	<div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
		<a
			href={resolve(routes.home)}
			class="inline-flex items-center rounded-md focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-white"
		>
			<img
				src="/images/logo_transparent.png"
				alt="Homeroom Heroes"
				width="298"
				height="95"
				class="h-12 w-auto sm:h-14"
			/>
		</a>

		<nav aria-label="Primary" class="hidden items-center gap-1 md:flex">
			{#each publicNavItems as item (item.href)}
				<a
					href={resolve(item.href as '/')}
					class={navLinkClass(item.href)}
					aria-current={isActive(item.href) ? 'page' : undefined}
				>
					{item.label}
				</a>
			{/each}
		</nav>

		<div class="hidden md:block">
			<a
				href={resolve(routes.login as '/')}
				class="inline-flex min-h-10 items-center justify-center rounded-md border border-white/60 px-4 text-sm font-semibold text-white transition hover:bg-white hover:text-green-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
			>
				Login
			</a>
		</div>

		<button
			type="button"
			class="inline-flex size-11 items-center justify-center rounded-md text-white transition hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white md:hidden"
			aria-controls="mobile-navigation"
			aria-expanded={isMenuOpen}
			aria-label={isMenuOpen ? 'Close navigation' : 'Open navigation'}
			onclick={() => (isMenuOpen = !isMenuOpen)}
		>
			{#if isMenuOpen}
				<svg
					aria-hidden="true"
					viewBox="0 0 24 24"
					class="size-6"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
				>
					<path d="M6 6l12 12M18 6L6 18" stroke-linecap="round" />
				</svg>
			{:else}
				<svg
					aria-hidden="true"
					viewBox="0 0 24 24"
					class="size-6"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
				>
					<path d="M4 7h16M4 12h16M4 17h16" stroke-linecap="round" />
				</svg>
			{/if}
		</button>
	</div>

	{#if isMenuOpen}
		<div id="mobile-navigation" class="border-t border-green-700 bg-white md:hidden">
			<nav aria-label="Mobile primary" class="mx-auto max-w-7xl space-y-1 px-4 py-3">
				{#each publicNavItems as item (item.href)}
					<a
						href={resolve(item.href as '/')}
						class={mobileLinkClass(item.href)}
						aria-current={isActive(item.href) ? 'page' : undefined}
						onclick={closeMenu}
					>
						{item.label}
					</a>
				{/each}
				<a
					href={resolve(routes.login as '/')}
					class="block rounded-md px-3 py-2 text-base font-semibold text-green-950 transition hover:bg-green-50"
					onclick={closeMenu}
				>
					Login
				</a>
			</nav>
		</div>
	{/if}
</header>
