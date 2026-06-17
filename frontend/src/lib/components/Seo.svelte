<script lang="ts">
	import { getCanonicalUrl, site } from '$lib/routes';

	let {
		title,
		description,
		path,
		image = site.defaultOgImage,
		noindex = false
	} = $props<{
		title: string;
		description: string;
		path: string;
		image?: string;
		noindex?: boolean;
	}>();

	let canonicalUrl = $derived(getCanonicalUrl(path));
	let ogImageUrl = $derived(getCanonicalUrl(image));
</script>

<svelte:head>
	<title>{title}</title>
	<meta name="description" content={description} />
	<link rel="canonical" href={canonicalUrl} />
	<meta property="og:site_name" content={site.name} />
	<meta property="og:title" content={title} />
	<meta property="og:description" content={description} />
	<meta property="og:type" content="website" />
	<meta property="og:url" content={canonicalUrl} />
	<meta property="og:image" content={ogImageUrl} />
	{#if noindex}
		<meta name="robots" content="noindex, nofollow" />
	{/if}
</svelte:head>
