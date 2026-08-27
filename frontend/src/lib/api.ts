import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface Skill {
  id: number;
  name: string;
  domain_id: number;
  parent_id?: number | null;
  description?: string | null;
}

export interface Company {
  id: number;
  name: string;
  description?: string | null;
  website?: string | null;
  is_verified: boolean;
  trust_score: number;
}

export interface Gig {
  id: number;
  title: string;
  description: string;
  budget_min?: number | null;
  budget_max?: number | null;
  duration_days?: number | null;
  is_boosted: boolean;
  company: Company;
  skills: Skill[];
  views: number;
  applications: number;
  created_at: string;
  score?: number | null;
}

export interface Mentor {
  id: number;
  full_name: string;
  bio?: string | null;
  availability: string;
  mentees_helped: number;
  rating: number;
  hourly_rate?: number | null;
  skills: Skill[];
  score?: number | null;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  bio?: string | null;
  trust_score: number;
  is_verified: boolean;
  interaction_count: number;
  created_at: string;
  skills: Skill[];
}

export interface RankedFeed {
  gigs: Gig[];
  mentors: Mentor[];
  companies: Company[];
}

export async function login(email: string, password: string) {
  const form = new URLSearchParams();
  form.append('username', email);
  form.append('password', password);
  const { data } = await api.post<{ access_token: string }>('/api/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  localStorage.setItem('token', data.access_token);
  return data;
}

export async function register(payload: {
  email: string;
  password: string;
  full_name: string;
  bio?: string;
  skill_ids?: number[];
}) {
  const { data } = await api.post<User>('/api/auth/register', payload);
  return data;
}

export async function getMe() {
  const { data } = await api.get<User>('/api/me');
  return data;
}

export async function getFeed() {
  const { data } = await api.get<RankedFeed>('/api/feed');
  return data;
}

export async function getSkills() {
  const { data } = await api.get<Skill[]>('/api/skills');
  return data;
}

export async function getGigs() {
  const { data } = await api.get<Gig[]>('/api/gigs');
  return data;
}

export async function getMentors() {
  const { data } = await api.get<Mentor[]>('/api/mentors');
  return data;
}

export async function updateSkills(skill_ids: number[]) {
  const { data } = await api.post<User>('/api/me/skills', { skill_ids });
  return data;
}

export async function logInteraction(
  target_type: string,
  target_id: number,
  interaction_type: string
) {
  await api.post('/api/interactions', { target_type, target_id, interaction_type });
}

export function logout() {
  localStorage.removeItem('token');
}

export default api;
