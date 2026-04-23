export interface Token {
  access_token: string;
  token_type: string;
}

export interface UserPublic {
  id: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  full_name: string | null;
  created_at: string | null;
}

export interface TagPublic {
  id: string;
  name: string;
  user_id: string;
}

export interface TagsPublic {
  data: TagPublic[];
  count: number;
}

export interface QuestionPublic {
  id: string;
  title: string;
  difficulty: number;
  content: string;
  answer: string | null;
  user_id: string;
  created_at: string | null;
  updated_at: string | null;
  tags: TagPublic[];
}

export interface QuestionsPublic {
  data: QuestionPublic[];
  count: number;
}

export interface ReviewSchedulePublic {
  id: string;
  question_id: string;
  user_id: string;
  interval_days: number;
  ease_factor: number;
  repetitions: number;
  next_review_at: string;
  last_reviewed_at: string | null;
}

export interface DueReview {
  question: QuestionPublic;
  review: ReviewSchedulePublic;
}

export interface QuestionCreate {
  title: string;
  content: string;
  answer?: string;
  difficulty?: number;
  tag_ids?: string[];
}
