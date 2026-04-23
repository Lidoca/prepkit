import type {
  Token,
  UserPublic,
  TagPublic,
  TagsPublic,
  QuestionPublic,
  QuestionsPublic,
  QuestionCreate,
  DueReview,
  ReviewSchedulePublic,
} from './types';

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token =
    typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;

  const headers: Record<string, string> = {};
  if (!(init.body instanceof URLSearchParams)) {
    headers['Content-Type'] = 'application/json';
  }
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`/api/v1${path}`, {
    ...init,
    headers: { ...headers, ...(init.headers as Record<string, string> | undefined) },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  auth: {
    login: (email: string, password: string) =>
      req<Token>('/login/access-token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username: email, password }),
      }),
  },

  users: {
    me: () => req<UserPublic>('/users/me'),
  },

  questions: {
    list: (params?: {
      tag_id?: string;
      difficulty?: number;
      skip?: number;
      limit?: number;
    }) => {
      const q = new URLSearchParams();
      if (params?.tag_id) q.set('tag_id', params.tag_id);
      if (params?.difficulty != null) q.set('difficulty', String(params.difficulty));
      if (params?.skip != null) q.set('skip', String(params.skip));
      if (params?.limit != null) q.set('limit', String(params.limit));
      const qs = q.toString();
      return req<QuestionsPublic>(`/questions/${qs ? '?' + qs : ''}`);
    },
    create: (data: QuestionCreate) =>
      req<QuestionPublic>('/questions/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    get: (id: string) => req<QuestionPublic>(`/questions/${id}`),
    update: (id: string, data: Partial<QuestionCreate & { tag_ids: string[] }>) =>
      req<QuestionPublic>(`/questions/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      req<{ message: string }>(`/questions/${id}`, { method: 'DELETE' }),
  },

  tags: {
    list: () => req<TagsPublic>('/tags/'),
    create: (data: { name: string }) =>
      req<TagPublic>('/tags/', { method: 'POST', body: JSON.stringify(data) }),
  },

  reviews: {
    due: () => req<DueReview[]>('/reviews/due'),
    submit: (questionId: string, quality: number) =>
      req<ReviewSchedulePublic>(`/reviews/${questionId}/submit`, {
        method: 'POST',
        body: JSON.stringify({ quality }),
      }),
  },
};
