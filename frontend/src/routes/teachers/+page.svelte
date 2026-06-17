<script lang="ts">
	import { resolve } from '$app/paths';
	import Alert from '$lib/components/Alert.svelte';
	import Button from '$lib/components/Button.svelte';
	import FormField from '$lib/components/FormField.svelte';
	import PageShell from '$lib/components/PageShell.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { routes } from '$lib/routes';
	import type { PageData } from './$types';

	let { data } = $props<{
		data: PageData;
	}>();

	let directory = $derived(data.directory);
	let selected = $derived(directory.applied_filters);
	let hasSelectedFilters = $derived(
		Boolean(selected.state || selected.county || selected.district || selected.school)
	);

	const selectClass =
		'block min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-950 shadow-sm focus:border-green-600 focus:outline-2 focus:outline-green-600';
</script>

<Seo
	title="Homeroom Heroes - Find Teachers"
	description="Search for teachers by state, county, district, and school, then choose a classroom to support."
	path={routes.teachers}
/>

<PageShell
	eyebrow="Donate"
	title="Find a Teacher"
	intro="Search by location and choose a classroom to support with supplies from a teacher wishlist."
>
	<div class="space-y-8">
		{#if data.backendUnavailable}
			<Alert variant="warning" title="Teacher directory unavailable">
				The backend API is not reachable from this frontend server. Start FastAPI on
				<code class="rounded bg-amber-100 px-1 py-0.5">http://localhost:8000</code>
				to load teacher filters and results.
			</Alert>
		{/if}

		<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
			<form method="GET" action={resolve(routes.teachers as '/')} class="space-y-5">
				<div class="grid gap-5 md:grid-cols-2">
					<FormField id="state" label="State">
						<select id="state" name="state" class={selectClass}>
							<option value="">Any state</option>
							{#each directory.filters.states as state (state)}
								<option value={state} selected={selected.state === state}>{state}</option>
							{/each}
						</select>
					</FormField>

					<FormField id="county" label="County">
						<select id="county" name="county" class={selectClass}>
							<option value="">Any county</option>
							{#each directory.filters.counties as county (county)}
								<option value={county} selected={selected.county === county}>{county}</option>
							{/each}
						</select>
					</FormField>
				</div>

				<div class="grid gap-5 md:grid-cols-2">
					<FormField id="district" label="School District">
						<select id="district" name="district" class={selectClass}>
							<option value="">Any district</option>
							{#each directory.filters.districts as district (district)}
								<option value={district} selected={selected.district === district}
									>{district}</option
								>
							{/each}
						</select>
					</FormField>

					<FormField id="school" label="School">
						<select id="school" name="school" class={selectClass}>
							<option value="">Any school</option>
							{#each directory.filters.schools as school (school)}
								<option value={school} selected={selected.school === school}>{school}</option>
							{/each}
						</select>
					</FormField>
				</div>

				<div class="flex flex-wrap gap-3">
					<Button type="submit">Find Teachers</Button>
					{#if hasSelectedFilters}
						<Button href={routes.teachers} variant="secondary">Clear Filters</Button>
					{/if}
				</div>
			</form>
		</section>

		<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
			<div class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
				<div>
					<h2 class="text-3xl font-bold tracking-normal text-green-800">Search Results</h2>
					<p class="mt-2 text-base text-slate-600">
						{directory.total}
						{directory.total === 1 ? 'teacher' : 'teachers'} found
					</p>
				</div>
			</div>

			{#if directory.teachers.length > 0}
				<div class="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
					{#each directory.teachers as teacher (teacher.url_id)}
						<a
							href={resolve(`/teacher/${encodeURIComponent(teacher.url_id)}` as '/')}
							class="rounded-lg border border-slate-200 bg-slate-50 p-5 shadow-sm transition hover:border-green-300 hover:bg-green-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-700"
						>
							<h3 class="text-xl font-bold tracking-normal text-slate-950">{teacher.name}</h3>
							<p class="mt-3 text-sm leading-6 text-slate-700">
								{#if teacher.school}
									<span class="block font-semibold">{teacher.school}</span>
								{/if}
								<span>
									{[teacher.district, teacher.county, teacher.state].filter(Boolean).join(', ')}
								</span>
							</p>
						</a>
					{/each}
				</div>
			{:else}
				<p
					class="mt-6 rounded-md border border-slate-200 bg-slate-50 p-5 text-center text-slate-700"
				>
					No teachers found for your selection. Please try different criteria.
				</p>
			{/if}
		</section>
	</div>
</PageShell>
