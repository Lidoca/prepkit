'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import type { QuestionPublic } from '@/lib/types';

const DIFFICULTY_LABELS: Record<number, string> = {
  1: '매우 쉬움',
  2: '쉬움',
  3: '보통',
  4: '어려움',
  5: '매우 어려움',
};

const DIFFICULTY_COLORS: Record<number, string> = {
  1: 'bg-green-100 text-green-700',
  2: 'bg-teal-100 text-teal-700',
  3: 'bg-yellow-100 text-yellow-700',
  4: 'bg-orange-100 text-orange-700',
  5: 'bg-red-100 text-red-700',
};

export default function QuestionsPage() {
  const router = useRouter();
  const [questions, setQuestions] = useState<QuestionPublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [answer, setAnswer] = useState('');
  const [difficulty, setDifficulty] = useState(3);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem('access_token')) {
      router.push('/login');
      return;
    }
    fetchQuestions();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function fetchQuestions() {
    try {
      const { data } = await api.questions.list();
      setQuestions(data);
    } catch {
      router.push('/login');
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const q = await api.questions.create({
        title,
        content,
        answer: answer || undefined,
        difficulty,
      });
      setQuestions((prev) => [q, ...prev]);
      setShowForm(false);
      setTitle('');
      setContent('');
      setAnswer('');
      setDifficulty(3);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('이 질문을 삭제하시겠습니까?')) return;
    await api.questions.delete(id);
    setQuestions((prev) => prev.filter((q) => q.id !== id));
    if (expanded === id) setExpanded(null);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
        불러오는 중...
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto p-6">
      <div className="flex items-center justify-between mb-5">
        <h1 className="text-lg font-semibold">
          질문{' '}
          <span className="text-gray-400 font-normal text-sm">
            {questions.length}개
          </span>
        </h1>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
        >
          {showForm ? '취소' : '+ 새 질문'}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="mb-5 p-5 border border-blue-200 rounded-xl bg-blue-50 space-y-3"
        >
          <h2 className="text-sm font-medium text-blue-900">새 질문</h2>
          <input
            placeholder="제목 *"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <textarea
            placeholder="내용 *"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            required
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
          <textarea
            placeholder="정답 (선택)"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-gray-700">난이도</label>
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(Number(e.target.value))}
              className="px-2 py-1.5 border border-gray-300 rounded-lg text-sm bg-white"
            >
              {[1, 2, 3, 4, 5].map((d) => (
                <option key={d} value={d}>
                  {d} · {DIFFICULTY_LABELS[d]}
                </option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {submitting ? '저장 중...' : '저장'}
          </button>
        </form>
      )}

      {questions.length === 0 ? (
        <div className="text-center py-16 text-gray-400 text-sm">
          질문이 없습니다. 새 질문을 추가해보세요.
        </div>
      ) : (
        <ul className="space-y-2">
          {questions.map((q) => (
            <li
              key={q.id}
              className="bg-white border border-gray-200 rounded-xl overflow-hidden"
            >
              <button
                className="w-full text-left px-4 py-3 flex items-center justify-between gap-3 hover:bg-gray-50 transition-colors"
                onClick={() => setExpanded(expanded === q.id ? null : q.id)}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span
                    className={`shrink-0 text-xs px-2 py-0.5 rounded-full ${DIFFICULTY_COLORS[q.difficulty]}`}
                  >
                    {q.difficulty}
                  </span>
                  <span className="text-sm font-medium truncate">{q.title}</span>
                </div>
                <span className="text-gray-300 text-xs shrink-0">
                  {expanded === q.id ? '▲' : '▼'}
                </span>
              </button>

              {expanded === q.id && (
                <div className="px-4 pb-4 border-t border-gray-100">
                  <p className="text-sm text-gray-600 leading-relaxed mt-3">
                    {q.content}
                  </p>
                  {q.answer && (
                    <div className="mt-3 p-3 bg-green-50 border border-green-100 rounded-lg">
                      <p className="text-xs font-medium text-green-700 mb-1">정답</p>
                      <p className="text-sm text-gray-700 leading-relaxed">
                        {q.answer}
                      </p>
                    </div>
                  )}
                  {q.tags.length > 0 && (
                    <div className="flex gap-1.5 mt-3">
                      {q.tags.map((t) => (
                        <span
                          key={t.id}
                          className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full"
                        >
                          {t.name}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="mt-3 flex justify-end">
                    <button
                      onClick={() => handleDelete(q.id)}
                      className="text-xs text-red-400 hover:text-red-600 transition-colors"
                    >
                      삭제
                    </button>
                  </div>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
