<script lang="ts">
	import { onMount } from 'svelte';
	import { resolve } from '$app/paths';
	import { apiFetch } from '$lib/api/client';
	import type { BackendProfile } from '$lib/api/types';
	import { publicNavItems, routes } from '$lib/routes';

	let { currentPath = routes.home, initialProfile = null } = $props<{
		currentPath?: string;
		initialProfile?: BackendProfile | null;
	}>();

	let isMenuOpen = $state(false);
	let isEnhanced = $state(false);
	let profile = $derived<BackendProfile | null>(initialProfile);
	let isLoggingOut = $state(false);
	let isAuthenticated = $derived(profile !== null);
	let visiblePublicNavItems = $derived(
		isAuthenticated
			? publicNavItems.filter((item) => item.href !== routes.register)
			: publicNavItems
	);
	let canValidate = $derived(profile?.user_role === 'teacher' || profile?.user_role === 'admin');
	let isAdmin = $derived(profile?.user_role === 'admin');

	onMount(() => {
		isEnhanced = true;
	});

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

	return `rounded-md px-3 py-2 text-base font-semibold transition lg:text-lg ${activeClass}`;
	}

	function mobileLinkClass(href: string): string {
		const activeClass = isActive(href)
			? 'bg-green-700 text-white'
			: 'text-green-950 hover:bg-green-50';

		return `block rounded-md px-3 py-2 text-base font-semibold transition ${activeClass}`;
	}

	async function logout() {
		isLoggingOut = true;
		try {
			await apiFetch<unknown>('/profile/logout/', { method: 'POST' });
			profile = null;
			window.location.href = routes.home;
		} catch {
			window.alert('We could not log you out. Please try again.');
		} finally {
			isLoggingOut = false;
		}
	}
</script>

<header
	class="bg-gradient-to-r from-green-700 to-green-900 text-white shadow-sm"
	data-header-enhanced={isEnhanced}
>
	<div class="mx-auto flex max-w-[1730px] items-center justify-between px-4 py-4 sm:px-6 md:py-6 lg:px-8">
		<a
			href={resolve(routes.home)}
			class="inline-flex items-center rounded-md focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-white"
		>
			<img
				src="/images/logo_transparent.png"
				alt="Homeroom Heroes"
				width="298"
				height="95"
			class="h-16 w-auto md:h-20"
			/>
		</a>

		<nav aria-label="Primary" class="hidden items-center gap-1 md:flex">
			{#each visiblePublicNavItems as item (item.href)}
				<a
					href={resolve(item.href as '/')}
					class={navLinkClass(item.href)}
					aria-current={isActive(item.href) ? 'page' : undefined}
				>
					{item.label}
				</a>
			{/each}
		</nav>

		<div class="hidden items-center gap-1 md:flex">
			{#if isAuthenticated}
				<a href={resolve(routes.teacher)} class={navLinkClass(routes.teacher)}>My Page</a>
				<a href={resolve(routes.forum)} class={navLinkClass(routes.forum)}>Forum</a>
				{#if canValidate}
					<a href={resolve(routes.validation)} class={navLinkClass(routes.validation)}>Validation</a
					>
				{/if}
				{#if isAdmin}
					<a href={resolve(routes.admin)} class={navLinkClass(routes.admin)}>Admin</a>
				{/if}
				<button
					type="button"
					disabled={isLoggingOut || !isEnhanced}
					class="inline-flex min-h-10 items-center justify-center rounded-md border border-white/60 px-4 text-sm font-semibold text-white transition hover:bg-white hover:text-green-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white disabled:opacity-60"
					onclick={() => void logout()}
				>
					{isLoggingOut ? 'Logging Out...' : 'Logout'}
				</button>
			{:else}
				<a
					href={resolve(routes.login as '/')}
					class="inline-flex min-h-10 items-center justify-center rounded-md border border-white/60 px-4 text-sm font-semibold text-white transition hover:bg-white hover:text-green-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
				>
					Login
				</a>
			{/if}
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
				{#each visiblePublicNavItems as item (item.href)}
					<a
						href={resolve(item.href as '/')}
						class={mobileLinkClass(item.href)}
						aria-current={isActive(item.href) ? 'page' : undefined}
						onclick={closeMenu}
					>
						{item.label}
					</a>
				{/each}
				{#if isAuthenticated}
					<a
						href={resolve(routes.teacher)}
						class={mobileLinkClass(routes.teacher)}
						onclick={closeMenu}>My Page</a
					>
					<a href={resolve(routes.forum)} class={mobileLinkClass(routes.forum)} onclick={closeMenu}
						>Forum</a
					>
					{#if canValidate}
						<a
							href={resolve(routes.validation)}
							class={mobileLinkClass(routes.validation)}
							onclick={closeMenu}>Validation</a
						>
					{/if}
					{#if isAdmin}
						<a
							href={resolve(routes.admin)}
							class={mobileLinkClass(routes.admin)}
							onclick={closeMenu}>Admin</a
						>
					{/if}
					<button
						type="button"
						disabled={isLoggingOut || !isEnhanced}
						class="block w-full rounded-md px-3 py-2 text-left text-base font-semibold text-green-950 transition hover:bg-green-50 disabled:opacity-60"
						onclick={() => void logout()}
					>
						{isLoggingOut ? 'Logging Out...' : 'Logout'}
					</button>
				{:else}
					<a
						href={resolve(routes.login as '/')}
						class="block rounded-md px-3 py-2 text-base font-semibold text-green-950 transition hover:bg-green-50"
						onclick={closeMenu}
					>
						Login
					</a>
				{/if}
			</nav>
		</div>
	{/if}
</header>
