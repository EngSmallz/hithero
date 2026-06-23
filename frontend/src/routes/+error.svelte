<script lang="ts">
	import { page } from '$app/state';
	import Button from '$lib/components/Button.svelte';
	import PageShell from '$lib/components/PageShell.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { routes } from '$lib/routes';

	const errorCopy: Record<number, { title: string; heading: string; message: string }> = {
		403: {
			title: '403 - Forbidden - Homeroom Heroes',
			heading: 'Forbidden',
			message: 'You do not have permission to access this page.'
		},
		404: {
			title: '404 - Page Does Not Exist - Homeroom Heroes',
			heading: 'Page Does Not Exist',
			message: 'The page you are looking for could not be found.'
		}
	};

	let copy = $derived(
		errorCopy[page.status] ?? {
			title: `${page.status} - Homeroom Heroes`,
			heading: page.error?.message || 'Something went wrong',
			message: 'Please try again or return to the homepage.'
		}
	);
</script>

<Seo title={copy.title} description={copy.message} path={page.url.pathname} noindex />

<PageShell narrow>
	<section
		class="mx-auto flex min-h-[52vh] max-w-2xl flex-col items-center justify-center text-center"
	>
		<p class="text-7xl font-extrabold tracking-normal text-red-600">{page.status}</p>
		<h1 class="mt-5 text-3xl font-bold tracking-normal text-slate-950 sm:text-4xl">
			{copy.heading}
		</h1>
		<p class="mt-4 text-lg leading-8 text-slate-700">{copy.message}</p>
		<div class="mt-8">
			<Button href={routes.home} size="lg">Go to Homepage</Button>
		</div>
	</section>
</PageShell>
