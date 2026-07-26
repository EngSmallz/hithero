<script lang="ts">
	import Button from '$lib/components/Button.svelte';
	import PageShell from '$lib/components/PageShell.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { routes } from '$lib/routes';

	const sections = [
		{
			title: 'Introduction',
			body: 'These terms and conditions govern your use of our website. By using our website, you accept these terms and conditions in full. If you disagree with these terms and conditions or any part of these terms and conditions, you must not use our website.'
		},
		{
			title: 'Charitable Mission & Board Discretion',
			body: 'Homeroom Heroes is a registered 501(c)(3) nonprofit organization. While our platform facilitates a bridge between donors and specific classroom wishlists, Homeroom Heroes maintains final discretion and control over the use of all donated resources. To maintain our charitable status, all donations made via this platform are considered contributions to Homeroom Heroes educational programs. Each project is vetted to ensure alignment with our mission; donors acknowledge that contributions are for charitable programs and are not intended as private gifts to individuals.'
		},
		{
			title: 'Tax-Deductibility & Gift-in-Kind Disclosures',
			body: 'Purchases made through third-party wishlists, including Amazon.com or Amazon.ca, are transactions between the user and the third-party retailer. For tax purposes, your retailer purchase receipt serves as proof of the fair market value of your gift-in-kind. Homeroom Heroes does not provide cash receipts for third-party purchases. No goods or services are provided by Homeroom Heroes to the donor in exchange for their contribution.'
		},
		{
			title: 'Intellectual Property Rights',
			body: 'Unless otherwise stated, we or our licensors own the intellectual property rights in the website and material on the website. Subject to the license below, all these intellectual property rights are reserved.'
		},
		{
			title: 'Changes to Terms and Conditions',
			body: 'We may revise these terms and conditions from time to time. Revised terms and conditions will apply to the use of our website from the date of publication on our website. Please check this page regularly to ensure you are familiar with the current version.'
		},
		{
			title: 'Amazon Affiliate Disclosure',
			body: 'As an Amazon Associate, we earn from qualifying purchases. All commissions earned through the Amazon Associates program are used exclusively to support the operational costs of Homeroom Heroes and to fund direct donations to classrooms.'
		},
		{
			title: 'FTC Compliance',
			body: 'To comply with FTC regulations, any affiliate links on our website will be clearly identified as such. We are committed to transparency and providing our users with accurate information.'
		}
	];

	const registrationSections = [
		{
			title: 'Registration & Verification',
			body: 'To register, you must provide accurate and complete information as prompted. You are responsible for maintaining the confidentiality of your account. We reserve the right to verify teacher employment status via provided institutional contact information.'
		},
		{
			title: 'Ownership of Donated Items',
			body: "All items fulfilled through Homeroom Heroes are the property of the educational institution, school, or district at which the registered teacher is employed. These items must remain with the school or district in the event of the teacher's departure, unless otherwise authorized in writing by school administration."
		},
		{
			title: 'User Content',
			body: 'You grant us a worldwide, non-exclusive, royalty-free license to use, reproduce, and display content you submit in connection with Homeroom Heroes. You agree not to post content that is unlawful, harmful, or otherwise objectionable.'
		},
		{
			title: 'User Conduct',
			body: 'You agree not to impersonate any person, attempt unauthorized access to our systems, or engage in automated data collection without prior written consent.'
		},
		{
			title: 'Termination',
			body: 'We reserve the right to suspend or terminate your account at any time and for any reason without notice or liability. Upon termination, you must cease all use of the website.'
		}
	];
</script>

<Seo
	title="Terms and Conditions - Homeroom Heroes"
	description="Read Homeroom Heroes terms for charitable contributions, wishlist purchases, user registration, AI use, and site disclaimers."
	path={routes.terms}
/>

<PageShell
	eyebrow="Legal"
	title="Terms and Conditions"
	intro="These terms explain how Homeroom Heroes handles charitable contributions, wishlist purchases, registration, and site use."
	narrow
>
	<div class="space-y-8">
		<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
			<div class="space-y-7">
				{#each sections as section (section.title)}
					<div>
						<h2 class="text-2xl font-bold tracking-normal text-green-800">{section.title}</h2>
						<p class="mt-3 text-lg leading-8 text-slate-700">{section.body}</p>
					</div>
				{/each}
			</div>

			<div class="mt-8 text-center">
				<Button href={routes.wishlistSetup} variant="secondary">View Wishlist Setup</Button>
			</div>
		</section>

		<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
			<h2 class="text-3xl font-bold tracking-normal text-green-800">
				User Registration Terms and Conditions
			</h2>
			<p class="mt-4 text-lg leading-8 text-slate-700">
				These terms and conditions govern your use of the Homeroom Heroes user registration process.
				By registering on our website, you agree to abide by these terms and conditions.
			</p>

			<div class="mt-7 space-y-7">
				{#each registrationSections as section (section.title)}
					<div>
						<h3 class="text-2xl font-bold tracking-normal text-green-800">{section.title}</h3>
						<p class="mt-3 text-lg leading-8 text-slate-700">{section.body}</p>
					</div>
				{/each}
			</div>
		</section>

		<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
			<h2 class="text-3xl font-bold tracking-normal text-green-800">AI Considerations</h2>
			<p class="mt-4 text-lg leading-8 text-slate-700">
				These terms and conditions govern the ability to use this site for AI training models.
			</p>
			<h3 class="mt-7 text-2xl font-bold tracking-normal text-green-800">Restrictions</h3>
			<p class="mt-3 text-lg leading-8 text-slate-700">
				No entity has permission to use the Homeroom Heroes site or data for AI models without the
				explicit written permission of the Board.
			</p>
		</section>

		<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
			<h2 class="text-3xl font-bold tracking-normal text-green-800">Disclaimer</h2>
			<p class="mt-4 text-lg leading-8 text-slate-700">
				The information provided on this website is for general informational purposes only. We make
				no representations or warranties of any kind about the completeness, accuracy, or
				availability of the information or products contained on the website. Any reliance you place
				on such information is strictly at your own risk.
			</p>
		</section>
	</div>
</PageShell>
