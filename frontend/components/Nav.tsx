'use client';

import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';

export default function Nav() {
  const router = useRouter();
  const pathname = usePathname();

  function logout() {
    localStorage.removeItem('access_token');
    router.push('/login');
  }

  const linkClass = (href: string) =>
    `text-sm transition-colors ${
      pathname.startsWith(href)
        ? 'text-gray-900 font-medium'
        : 'text-gray-500 hover:text-gray-900'
    }`;

  return (
    <nav className="border-b border-gray-200 bg-white px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-6">
        <Link href="/questions" className="font-bold text-sm tracking-tight">
          prepkit
        </Link>
        <Link href="/questions" className={linkClass('/questions')}>
          질문
        </Link>
        <Link href="/reviews" className={linkClass('/reviews')}>
          복습
        </Link>
      </div>
      <button
        onClick={logout}
        className="text-xs text-gray-400 hover:text-gray-700 transition-colors"
      >
        로그아웃
      </button>
    </nav>
  );
}
