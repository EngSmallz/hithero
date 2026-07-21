<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import Alert from '$lib/components/Alert.svelte';
	import Button from '$lib/components/Button.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { apiFetch, getBackendOrigin } from '$lib/api/client';
	import type { UserRole } from '$lib/api/types';
	import { routes } from '$lib/routes';
	import { buildWishlistUrl } from '$lib/wishlist';
	import type { PageData } from './$types';

	type StatusVariant = 'info' | 'success' | 'warning' | 'error';
	type StatusMessage = { variant: StatusVariant; message: string };
	type ApiMessage = { detail?: string; message?: string; url?: string };
	type ProfileResponse = {
		user_role?: UserRole;
		user_id?: number | string;
		user_email?: string;
	};
	type TeacherProfile = {
		state?: string | null;
		county?: string | null;
		district?: string | null;
		school?: string | null;
		name?: string | null;
		wishlist_url?: string | null;
		about_me?: string | null;
		image_data?: string | null;
	};

	let { data } = $props<{ data: PageData }>();

	const backendOrigin = getBackendOrigin();
	const defaultTeacherImage = new URL('/static/images/apple.jpg', backendOrigin).toString();
	const MAX_FILE_SIZE_MB = 1;
	const regionStateMap: Record<string, string> = {
		Washington: 'PNW',
		Oregon: 'PNW',
		Idaho: 'PNW',
		California: 'Cali',
		Utah: 'Rocky_Mountians',
		Montana: 'Rocky_Mountians',
		Colorado: 'Rocky_Mountians',
		Nevada: 'South_West',
		Arizona: 'South_West',
		'New Mexico': 'South_West',
		Texas: 'South_Central',
		Oklahoma: 'South_Central',
		Wyoming: 'South_Central',
		'North Dakota': 'Plains',
		'South Dakota': 'Plains',
		Nebraska: 'Plains',
		Kansas: 'Plains',
		Minnesota: 'Plains',
		Iowa: 'Plains',
		Missouri: 'Lower_Mississippi',
		Arkansas: 'Lower_Mississippi',
		Tennessee: 'Lower_Mississippi',
		Mississippi: 'Lower_Mississippi',
		Louisiana: 'Lower_Mississippi',
		Michigan: 'Great_Lakes',
		Wisconsin: 'Great_Lakes',
		Illinois: 'Great_Lakes',
		Indiana: 'Great_Lakes',
		Ohio: 'Great_Lakes',
		Pennsylvania: 'MidEast',
		'New York': 'MidEast',
		'New Jersey': 'MidEast',
		Delaware: 'MidEast',
		Maryland: 'MidEast',
		'West Virginia': 'MidEast',
		Kentucky: 'South_East',
		'North Carolina': 'South_East',
		'South Carolina': 'South_East',
		Georgia: 'South_East',
		Alabama: 'South_East',
		Virginia: 'South_East',
		Florida: 'Florida',
		Maine: 'New_England',
		Vermont: 'New_England',
		'New Hampshire': 'New_England',
		Massachusetts: 'New_England',
		'Rhode Island': 'New_England',
		Connecticut: 'New_England',
		Alaska: 'Alaska',
		Hawaii: 'Hawaii',
		'District Of Columbia': 'DC',
		'Puerto Rico': 'US-Caribbean',
		'Virgin Islands': 'US-Caribbean',
		Guam: 'US-Pacific',
		'Northern Mariana Islands': 'US-Pacific',
		'American Samoa': 'US-Pacific',
		'Armed Forces Africa': 'Armed-Forces',
		'Armed Forces Americas': 'Armed-Forces',
		'Armed Forces Canada': 'Armed-Forces',
		'Armed Forces Europe': 'Armed-Forces',
		'Armed Forces Middle East': 'Armed-Forces',
		'Armed Forces Pacific': 'Armed-Forces'
	};

	const initialData = untrack(() => data);
	let teacher = $state<TeacherProfile | null>(initialData.teacher);
	let currentProfile = $derived<ProfileResponse | null>(data.profile);
	let isLoading = $state(initialData.currentTeacherState === 'session-selected');
	let isOwner = $state(
		Boolean(
			initialData.teacher &&
			(initialData.profile?.user_role === 'teacher' || initialData.profile?.user_role === 'admin')
		)
	);
	let isUploadingImage = $state(false);
	let status = $state<StatusMessage | null>(
		initialData.currentTeacherState === 'backend-unavailable'
			? { variant: 'error', message: 'Teacher profiles are temporarily unavailable.' }
			: initialData.currentTeacherState === 'not-found'
				? { variant: 'warning', message: 'Your account does not have a teacher profile yet.' }
				: null
	);
	let imageInput = $state<HTMLInputElement | null>(null);

	let teacherName = $derived(teacher?.name?.trim() || 'Teacher Profile');
	let teacherImageSrc = $derived(
		teacher?.image_data ? `data:image/jpeg;base64,${teacher.image_data}` : defaultTeacherImage
	);
	let locationText = $derived(
		[teacher?.county, teacher?.state].filter(Boolean).join(', ') || 'Location unavailable'
	);
	let schoolText = $derived(teacher?.school || 'School unavailable');
	let regionImageUrl = $derived(getRegionImageUrl(teacher?.state));
	let profileHeaderStyle = $derived(
		regionImageUrl
			? `background-image: linear-gradient(rgba(255,255,255,0.56), rgba(255,255,255,0.56)), url("${regionImageUrl}"); background-size: cover; background-position: center;`
			: ''
	);
	let seoTitle = $derived(
		teacher?.name
			? `${teacher.name} - Homeroom Heroes Teacher Profile`
			: 'Teacher Profile - Homeroom Heroes'
	);
	let seoDescription = $derived(
		teacher?.name
			? `Support ${teacher.name}'s classroom wishlist through Homeroom Heroes.`
			: 'View a Homeroom Heroes teacher profile and classroom wishlist.'
	);

	onMount(() => {
		if (initialData.currentTeacherState === 'session-selected') {
			void loadTeacherPage();
		}
	});

	async function loadTeacherPage() {
		isLoading = true;
		status = { variant: 'info', message: 'Loading teacher profile...' };
		isOwner = false;

		const loadedTeacher = await tryFetchTeacherInfo();

		if (!loadedTeacher) {
			teacher = null;
			status = {
				variant: 'error',
				message: 'Teacher profile could not be loaded. Please open a valid teacher link.'
			};
			isLoading = false;
			return;
		}

		teacher = loadedTeacher;
		status = null;
		isLoading = false;
		await updateOwnerAccess();
	}

	async function tryFetchTeacherInfo(): Promise<TeacherProfile | null> {
		try {
			return await apiFetch<TeacherProfile>('/api/get_teacher_info/');
		} catch (error) {
			console.error('Error fetching teacher info:', error);
			return null;
		}
	}

	async function updateOwnerAccess() {
		if (currentProfile?.user_role === 'admin') {
			isOwner = true;
			return;
		}

		if (currentProfile?.user_role !== 'teacher') {
			isOwner = false;
			return;
		}

		try {
			await apiFetch<unknown>('/api/check_access_teacher/');
			isOwner = true;
		} catch (error) {
			console.error('Error checking teacher access:', error);
			isOwner = false;
		}
	}

	function openImagePicker() {
		imageInput?.click();
	}

	async function updateImage(event: Event) {
		const input = event.currentTarget;
		if (!(input instanceof HTMLInputElement)) {
			return;
		}

		const selectedFile = input.files?.[0];
		if (!selectedFile) {
			return;
		}

		if (selectedFile.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
			window.alert(
				`File size exceeds the allowed limit of ${MAX_FILE_SIZE_MB}MB. Please upload a smaller image.`
			);
			input.value = '';
			return;
		}

		const formData = new FormData();
		formData.append('image', selectedFile);
		isUploadingImage = true;

		try {
			await apiFetch<unknown>('/profile/update_teacher_image/', {
				method: 'POST',
				body: formData
			});

			window.location.reload();
		} catch (error) {
			const message =
				error instanceof Error ? error.message : 'An error occurred while updating teacher image.';
			console.error(`Error updating teacher image: ${message}`);
			window.alert(`Error updating teacher image: ${message}`);
		} finally {
			isUploadingImage = false;
			input.value = '';
		}
	}

	async function sharePage() {
		try {
			const data = await apiFetch<ApiMessage>('/api/teacher_url/');
			if (!data.url) {
				throw new Error('Teacher URL was not returned.');
			}

			const shareUrl = new URL(data.url, window.location.origin).toString();
			await navigator.clipboard.writeText(shareUrl);
			window.alert('Teacher URL has been copied to clipboard!');
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Unable to share this teacher page.';
			console.error('Error:', error);
			window.alert(`Error: ${message}`);
		}
	}

	function titleCaseWords(value: string): string {
		return value
			.trim()
			.split(/\s+/)
			.map((word) => word.charAt(0).toUpperCase() + word.slice(1))
			.join(' ');
	}

	function getRegionImageUrl(state?: string | null): string {
		if (!state) {
			return '';
		}

		const regionName = regionStateMap[titleCaseWords(state)];
		return regionName
			? new URL(`/static/images/regions/${regionName}.jpg`, backendOrigin).toString()
			: '';
	}
</script>

<Seo title={seoTitle} description={seoDescription} path={routes.teacher} noindex />

<div class="mx-auto w-full max-w-5xl px-4 py-10 sm:px-6 sm:py-14 lg:px-8">
	<noscript>
		<div
			class="mx-auto mb-6 max-w-3xl rounded-md border border-amber-200 bg-amber-50 p-4 text-amber-950"
			role="alert"
		>
			Image updates and Share Page require JavaScript. Profile details, wishlist links, and account
			settings remain available without it.
		</div>
	</noscript>

	{#if status}
		<div class="mx-auto mb-6 max-w-3xl">
			<Alert variant={status.variant}>{status.message}</Alert>
		</div>
	{/if}

	{#if teacher}
		<div class="space-y-8" aria-busy={isLoading}>
			<section
				class="overflow-hidden rounded-lg border border-slate-200 bg-white p-6 text-slate-950 shadow-sm sm:p-8"
				style={profileHeaderStyle}
			>
				<div class="flex flex-col items-center gap-6 text-center">
					<div class="flex flex-col items-center">
						<img
							src={teacherImageSrc}
							alt={`${teacherName} profile`}
							class="size-44 rounded-full border-4 border-green-600 bg-white object-cover shadow-lg sm:size-48"
						/>
						{#if isOwner}
							<input
								bind:this={imageInput}
								type="file"
								accept="image/jpeg,image/png"
								class="hidden"
								onchange={updateImage}
							/>
							<Button
								type="button"
								variant="secondary"
								class="mt-4 w-full"
								disabled={isUploadingImage}
								onclick={openImagePicker}
							>
								{isUploadingImage ? 'Updating Image...' : 'Update Image'}
							</Button>
						{/if}
					</div>

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
							href={buildWishlistUrl(teacher.wishlist_url)}
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
					{teacher.about_me || ''}
				</p>
			</section>

			<div class="mx-auto grid max-w-md gap-3">
				{#if isOwner}
					<Button href={routes.profileEdit} class="w-full">Edit Info</Button>
					<Button href={routes.updatePassword} variant="secondary" class="w-full">
						Update Password
					</Button>
				{/if}
				<Button type="button" variant="secondary" class="w-full" onclick={() => void sharePage()}>
					Share Page
				</Button>
			</div>
		</div>
	{:else if initialData.currentTeacherState === 'not-found' && currentProfile}
		<section
			class="mx-auto max-w-3xl rounded-lg border border-green-200 bg-white p-8 text-center shadow-sm sm:p-10"
		>
			<h1 class="text-3xl font-bold tracking-normal text-green-900 sm:text-4xl">
				Create your teacher profile
			</h1>
			<p class="mx-auto mt-4 max-w-2xl text-lg leading-8 text-slate-700">
				Your account is approved. Add your school, classroom details, and wishlist so supporters can
				find you.
			</p>
			<Button href={routes.profileCreate} class="mt-6">Create Teacher Profile</Button>
		</section>
	{/if}
</div>
