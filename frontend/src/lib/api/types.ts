export type ApiErrorBody = {
	detail?: string;
	message?: string;
};

export type ApiResult<T> = {
	data: T;
};

export type PaginatedResult<T> = {
	items: T[];
	total: number;
};

export type UserRole = 'admin' | 'teacher' | 'user';

export type AuthSession = {
	isAuthenticated: boolean;
	role?: UserRole;
	userId?: number;
};

export type BackendProfile = {
	user_role: UserRole;
	user_id: number | string;
	user_email: string;
};

export type TeacherSummary = {
	name: string;
	url_id: string;
	state?: string | null;
	county?: string | null;
	district?: string | null;
	school?: string | null;
};

export type TeacherProfile = TeacherSummary & {
	wishlist_url?: string | null;
	about_me?: string | null;
	image_data?: string | null;
};

export type TeacherDirectoryFilters = {
	states: string[];
	counties: string[];
	districts: string[];
	schools: string[];
};

export type TeacherDirectoryResponse = {
	teachers: TeacherSummary[];
	filters: TeacherDirectoryFilters;
	total: number;
	page: number;
	page_size: number;
	total_pages: number;
	applied_filters: {
		state?: string | null;
		county?: string | null;
		district?: string | null;
		school?: string | null;
	};
};
