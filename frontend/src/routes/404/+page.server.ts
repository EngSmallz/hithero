import { error } from '@sveltejs/kit';

export const load = () => {
	error(404, 'Page Does Not Exist');
};
