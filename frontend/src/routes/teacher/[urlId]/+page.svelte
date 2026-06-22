<script lang="ts">
	import { getBackendOrigin } from '$lib/api/client';
	import Button from '$lib/components/Button.svelte';
	import PageShell from '$lib/components/PageShell.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { routes } from '$lib/routes';
	import type { PageData } from './$types';

	let { data } = $props<{ data: PageData }>();

	const backendOrigin = getBackendOrigin();
	const defaultTeacherImage = new URL('/static/images/apple.jpg', backendOrigin).toString();

	let teacher = $derived(data.teacher);
	let teacherName = $derived(teacher.name?.trim() || 'Teacher Profile');
	let teacherImageSrc = $derived(
		teacher.image_data ? `data:image/jpeg;base64,${teacher.image_data}` : defaultTeacherImage
	);
	let locationText = $derived(
		[teacher.county, teacher.state].filter(Boolean).join(', ') || 'Location unavailable'
	);
	let schoolText = $derived(teacher.school || 'School unavailable');
	let canonicalPath = $derived(`${routes.teacher}/${encodeURIComponent(teacher.url_id)}`);
	let seoTitle = $derived(`${teacherName} - Homeroom Heroes Teacher Profile`);
	let seoDescription = $derived(
		`Support ${teacherName}'s classroom wishlist through Homeroom Heroes.`
	);

	function copyProfileUrl() {
		if (typeof window === 'undefined') {
			return;
		}

		void navigator.clipboard
			.writeText(window.location.href)
			.then(() => window.alert('Teacher URL has been copied to clipboard!'))
			.catch(() => window.alert('Unable to copy this teacher page link.'));
	}
</script>

<Seo title={seoTitle} description={seoDescription} path={canonicalPath} />

<PageShell narrow>
	<article class="space-y-8">
		<section
			class="overflow-hidden rounded-lg border border-slate-200 bg-white p-6 text-slate-950 shadow-sm sm:p-8"
		>
			<div class="flex flex-col items-center gap-6 text-center">
				<img
					src={teacherImageSrc}
					alt={`${teacherName} profile`}
					class="size-44 rounded-full border-4 border-green-600 bg-white object-cover shadow-lg sm:size-48"
				/>

				<div>
					<h1 class="text-4xl font-bold tracking-normal text-green-900 sm:text-5xl">
						{teacherName}
					</h1>
					<p class="mt-3 text-xl font-bold text-slate-950">School: {schoolText}</p>
					<p class="mt-1 text-lg font-bold text-slate-950">Location: {locationText}</p>
				</div>

				{#if teacher.wishlist_url}
					<!-- eslint-disable svelte/no-navigation-without-resolve -->
					<a
						href={teacher.wishlist_url}
						target="_blank"
						rel="noopener noreferrer"
						class="inline-flex min-h-12 items-center justify-center rounded-full bg-yellow-500 px-8 text-xl font-bold text-slate-950 shadow-sm transition hover:bg-yellow-600 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-yellow-600"
					>
						View Wishlist
					</a>
					<!-- eslint-enable svelte/no-navigation-without-resolve -->
				{/if}
			</div>
		</section>

		<section
			class="rounded-lg border border-slate-200 bg-white p-6 text-slate-950 shadow-sm sm:p-8"
		>
			<h2 class="text-center text-3xl font-bold tracking-normal text-green-800">About Me</h2>
			<p class="mt-5 whitespace-pre-wrap text-lg leading-8 text-slate-700">
				{teacher.about_me || 'This teacher has not added a classroom story yet.'}
			</p>
		</section>

		<div class="mx-auto grid max-w-md gap-3">
			<Button type="button" variant="secondary" class="w-full" onclick={copyProfileUrl}>
				Share Page
			</Button>
			<Button href={routes.teachers} variant="secondary" class="w-full">Find More Teachers</Button>
		</div>
	</article>
</PageShell>
