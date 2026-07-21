import { env } from '$env/dynamic/public';

type RecaptchaApi = {
	render: (container: HTMLElement, options: { sitekey: string }) => number;
	getResponse: (widgetId?: number) => string;
	reset: (widgetId?: number) => void;
};

const LOCAL_RECAPTCHA_TOKEN = 'hithero-test-recaptcha';

export function isRecaptchaMock(): boolean {
	return env.PUBLIC_RECAPTCHA_MODE === 'mock';
}

declare global {
	interface Window {
		grecaptcha?: RecaptchaApi;
	}
}

const scriptSelector = 'script[data-recaptcha-script]';

async function loadRecaptcha(): Promise<RecaptchaApi> {
	if (window.grecaptcha?.render) {
		return window.grecaptcha;
	}

	let script = document.querySelector<HTMLScriptElement>(scriptSelector);
	let shouldAppend = false;
	if (!script) {
		script = document.createElement('script');
		script.src = 'https://www.google.com/recaptcha/api.js?render=explicit';
		script.async = true;
		script.defer = true;
		script.dataset.recaptchaScript = 'true';
		shouldAppend = true;
	}

	await new Promise<void>((resolve, reject) => {
		const finish = () => {
			if (window.grecaptcha?.render) {
				resolve();
			} else {
				reject(new Error('reCAPTCHA did not initialize.'));
			}
		};

		if (script.dataset.loaded === 'true') {
			finish();
			return;
		}

		script.addEventListener(
			'load',
			() => {
				script.dataset.loaded = 'true';
				finish();
			},
			{ once: true }
		);
		script.addEventListener('error', () => reject(new Error('reCAPTCHA could not be loaded.')), {
			once: true
		});

		if (shouldAppend) {
			document.head.appendChild(script);
		}
	});

	if (!window.grecaptcha) {
		throw new Error('reCAPTCHA did not initialize.');
	}
	return window.grecaptcha;
}

export async function renderRecaptcha(container: HTMLElement, sitekey: string): Promise<number> {
	if (isRecaptchaMock()) {
		return -1;
	}

	const recaptcha = await loadRecaptcha();
	return recaptcha.render(container, { sitekey });
}

export function getRecaptchaResponse(widgetId: number | null, mockAccepted = false): string {
	if (isRecaptchaMock()) {
		return mockAccepted ? LOCAL_RECAPTCHA_TOKEN : '';
	}

	return widgetId === null ? '' : (window.grecaptcha?.getResponse(widgetId) ?? '');
}

export function resetRecaptcha(widgetId: number | null): void {
	if (widgetId !== null && !isRecaptchaMock()) {
		window.grecaptcha?.reset(widgetId);
	}
}
