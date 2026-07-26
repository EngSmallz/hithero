<script lang="ts">
	import Button from '$lib/components/Button.svelte';
	import PageShell from '$lib/components/PageShell.svelte';
	import Seo from '$lib/components/Seo.svelte';
	import { routes } from '$lib/routes';

	const description =
		'Learn about Homeroom Heroes, a 501(c) registered charity supporting educators and classrooms across the nation.';

	const teamMembers = [
		{
			name: 'Justin Brundage',
			role: 'Founder, CEO, & President',
			image: '/images/about/peanut.jpg',
			alt: 'Justin Brundage',
			bio: [
				"I'm Justin Brundage, Founder and CEO of Homeroom Heroes. My journey began in August 2023, where I was inspired by a local radio station's effort to support teachers by fulfilling their classroom wish lists. Witnessing the financial burden teachers face - spending an average of $850 of their own money on supplies in 2023 - drove me to create Homeroom Heroes.",
				'Growing up in a close-knit community, I experienced firsthand the profound impact teachers have on shaping lives. Recognizing their invaluable contributions, I embarked on a mission to give back. Armed with a degree in Material Science and Engineering from Washington State University, I founded Homeroom Heroes to revolutionize support for educators. Our platform connects teachers directly with the resources they need, empowering communities to rally behind their local heroes and ensure every classroom has the tools to inspire future generations.',
				'Join me in honoring the dedication of our teachers and making a lasting impact on education.'
			]
		},
		{
			name: 'Sam Mahan',
			role: 'Co-Founder, CTO, & Treasurer',
			image: '/images/about/grape.jpg',
			alt: 'Sam Mahan',
			bio: [
				"I'm Samuel Mahan, a software engineer dedicated to driving technological innovation and making a meaningful impact in the industry. With a background in Electrical and Electronics Engineering from Washington State University, I've honed my skills through various roles, including software development at Amazon and Adaptiva. My journey in the tech world began with a passion for problem-solving and a relentless drive to learn and adapt. Justin and I met during our freshman year at Washington State University, where our shared curiosity for technology sparked a lasting friendship and collaborative spirit. Today, I leverage my expertise to create robust backend services and firmware solutions, ensuring optimal performance and reliability. I'm committed to pushing boundaries and embracing new technologies to drive forward progress in the ever-evolving landscape of software engineering."
			]
		},
		{
			name: 'Tory Furr',
			role: 'COO & Secretary of the Board',
			image: '/images/about/Tory.jpg',
			alt: 'Tory Furr',
			bio: [
				"Born and raised in the Pacific Northwest, I've seen firsthand the struggles many families face. Through my work as a property manager for income-restricted housing, I've witnessed the direct and profound impact that a good education has on a child's future. This experience ignited my passion for helping others, inspiring me to join Homeroom Heroes. My dedication to our community extends beyond my professional life, and in my free time, you can find me enjoying crafts, video games, hiking, and baking. I believe that by supporting our teachers, we're not just providing supplies; we're investing in the lives of our students and building a stronger, more resilient community for everyone."
			]
		},
		{
			name: 'Jillian Ortega',
			role: 'Board Member',
			image: '/images/about/jillian.jpg',
			alt: 'Jillian Ortega',
			bio: [
				'I am Jillian Ortega, an electrical engineer, a wife, and a mother of two children. As my children are nearing the age to enter the public school system, the quality of education and access to the tools they need to learn and thrive has become paramount. That is why I am honored to join this organization on the board of directors. I look forward to serving this community to the best of my abilities.'
			]
		}
	];
</script>

<Seo title="Homeroom Heroes - About Us" {description} path={routes.about} />

<PageShell
	eyebrow="About Homeroom Heroes"
	title="About Us"
	intro="We are Homeroom Heroes, a 501(c) registered charity dedicated to supporting educators and enriching classrooms across the nation."
>
	<div class="space-y-8">
		<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
			<h2 class="text-3xl font-bold tracking-normal text-green-800">Our Mission</h2>
			<p class="mt-4 text-lg leading-8 text-slate-700">
				At Homeroom Heroes, our mission is to serve as a pivotal bridge between educators and
				community supporters, fostering meaningful connections that enhance educational experiences.
				With a steadfast commitment to the transformative power of education, we empower teachers by
				providing a platform to articulate their needs and aspirations, while enabling compassionate
				individuals to directly contribute to the enrichment of classrooms nationwide. Through our
				collaborative efforts, we strive to cultivate a brighter future for generations to come, one
				classroom at a time.
			</p>
		</section>

		<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
			<h2 class="text-3xl font-bold tracking-normal text-green-800">How Do We Do That?</h2>
			<p class="mt-4 text-lg leading-8 text-slate-700">
				At Homeroom Heroes, we simplify the process for teachers to showcase their needs by creating
				profiles and hosting curated wishlists of essential classroom supplies through Amazon. Our
				platform enables community members to make a direct impact by selecting and sending items
				straight to teachers' classrooms, with no middlemen and no extra fees. Every donation
				directly supports students by enhancing their learning environments. Together, we bridge the
				gap between community generosity and classroom success.
			</p>
		</section>

		<section
			class="rounded-lg border border-green-200 bg-green-50 p-6 shadow-sm sm:flex sm:items-center sm:justify-between sm:gap-6 sm:p-8"
		>
			<div>
				<h2 class="text-2xl font-bold tracking-normal text-green-900">
					Website Terms and Conditions
				</h2>
				<p class="mt-2 max-w-2xl text-base leading-7 text-green-950">
					Review how Homeroom Heroes handles charitable contributions, wishlist purchases, and user
					registration expectations.
				</p>
			</div>
			<Button href={routes.terms} class="mt-5 sm:mt-0">Terms and Conditions</Button>
		</section>

		<section class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
			<div class="mx-auto max-w-3xl text-center">
				<h2 class="text-3xl font-bold tracking-normal text-green-800">Meet the Team</h2>
				<p class="mt-4 text-lg leading-8 text-slate-700">
					We are a team dedicated to making a positive impact on education. Get to know the
					individuals behind the project.
				</p>
			</div>

			<div class="mt-8 grid gap-6 md:grid-cols-2">
				{#each teamMembers as member (member.name)}
					<article class="rounded-lg border border-slate-200 bg-slate-50 p-5 text-center">
						<img
							src={member.image}
							alt={member.alt}
							width="160"
							height="160"
							class="mx-auto size-32 rounded-full border-4 border-green-200 object-cover"
							loading="lazy"
						/>
						<h3 class="mt-4 text-xl font-bold tracking-normal text-green-800">
							{member.name}
						</h3>
						<p class="mt-2 text-base font-semibold text-slate-700">{member.role}</p>
						<div class="mt-4 space-y-3 text-left text-base leading-7 text-slate-700">
							{#each member.bio as paragraph (paragraph)}
								<p>{paragraph}</p>
							{/each}
						</div>
					</article>
				{/each}
			</div>
		</section>
	</div>
</PageShell>
