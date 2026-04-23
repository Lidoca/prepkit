'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import type { DueReview } from '@/lib/types';

const QUALITY_OPTIONS = [
  { label: '완전 모름', value: 0, color: 'border-red-200 bg-red-50 text-red-700 hover:bg-red-100' },
  { label: '잘 모름', value: 1, color: 'border-red-200 bg-red-50 text-red-700 hover:bg-red-100' },
  { label: '어렴풋이', value: 2, color: 'border-orange-200 bg-orange-50 text-orange-700 hover:bg-orange-100' },
  { label: '기억남', value: 3, color: 'border-yellow-200 bg-yellow-50 text-yellow-700 hover:bg-yellow-100' },
  { label: '잘 앎', value: 4, color: 'border-green-200 bg-green-50 text-green-700 hover:bg-green-100' },
  { label: '완벽', value: 5, color: 'border-green-200 bg-green-50 text-green-700 hover:bg-green-100' },
];

export default function ReviewsPage() {
  const router = useRouter();
  const [reviews, setReviews] = useState<DueReview[]>([]);
  const [current, setCurrent] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem('access_token')) {
      router.push('/login');
      return;
    }
    api.reviews
      .due()
      .then((data) => {
        setReviews(data);
        setLoading(false);
      })
      .catch(() => router.push('/login'));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleQuality(quality: number) {
    const review = reviews[current];
    setSubmitting(true);
    try {
      await api.reviews.submit(review.question.id, quality);
      if (current + 1 >= reviews.length) {
        setDone(true);
      } else {
        setCurrent((c) => c + 1);
        setShowAnswer(false);
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
        불러오는 중...
      </div>
    );
  }

  if (done || reviews.length === 0) {
    return (
      <div className="max-w-2xl mx-auto p-6 text-center">
        <div className="py-20">
          <p className="text-5xl mb-4">🎉</p>
          <h2 className="text-xl font-semibold mb-2">오늘 복습 완료!</h2>
          <p className="text-gray-500 text-sm mt-1">
            {reviews.length === 0
              ? '오늘 복습할 질문이 없습니다.'
              : `${reviews.length}개 질문을 복습했습니다.`}
          </p>
          <button
            onClick={() => router.push('/questions')}
            className="mt-6 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
          >
            질문 목록으로
          </button>
        </div>
      </div>
    );
  }

  const { question, review } = reviews[current];
  const progress = (current / reviews.length) * 100;

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-semibold">복습</h1>
        <span className="text-sm text-gray-400">
          {current + 1} / {reviews.length}
        </span>
      </div>

      <div className="mb-4 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-500 transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <div className="flex gap-2 mb-4">
          <span className="text-xs px-2 py-0.5 bg-gray-100 rounded-full text-gray-600">
            난이도 {question.difficulty}
          </span>
          <span className="text-xs px-2 py-0.5 bg-blue-100 rounded-full text-blue-700">
            {review.repetitions}회 복습 · 간격 {review.interval_days}일
          </span>
        </div>

        <h2 className="font-semibold text-base mb-3">{question.title}</h2>
        <p className="text-gray-600 text-sm leading-relaxed">{question.content}</p>

        {!showAnswer ? (
          <button
            onClick={() => setShowAnswer(true)}
            className="mt-5 w-full py-2.5 border-2 border-dashed border-gray-300 text-sm text-gray-500 rounded-lg hover:border-gray-400 hover:text-gray-600 transition-colors"
          >
            정답 보기
          </button>
        ) : (
          <div className="mt-5">
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-xs font-medium text-green-700 mb-1.5">정답</p>
              <p className="text-sm text-gray-700 leading-relaxed">
                {question.answer ?? '정답이 등록되지 않았습니다.'}
              </p>
            </div>

            <div className="mt-5">
              <p className="text-xs text-gray-500 mb-2.5 font-medium">
                얼마나 잘 기억했나요?
              </p>
              <div className="grid grid-cols-3 gap-2">
                {QUALITY_OPTIONS.map(({ label, value, color }) => (
                  <button
                    key={value}
                    onClick={() => handleQuality(value)}
                    disabled={submitting}
                    className={`py-2 px-2 text-xs rounded-lg border transition-colors disabled:opacity-50 ${color}`}
                  >
                    <span className="block font-medium">{value}</span>
                    <span className="block mt-0.5 text-[11px] opacity-80">{label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
