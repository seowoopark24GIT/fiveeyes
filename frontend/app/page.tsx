"use client";

import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();

  return (
    <main className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-xl bg-white rounded-2xl shadow-xl border border-gray-100 px-8 py-10">
        <header className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-gray-900">
              FiveEyes
            </h1>
            <p className="mt-1 text-xs text-gray-500">
              점자 의약품 출력 정보를 관리하는 관리자 · 약사용 도구
            </p>
          </div>
          <span className="inline-flex items-center justify-center rounded-full bg-blue-50 px-3 py-1 text-[11px] font-medium text-blue-700">
            v1.0
          </span>
        </header>

        <section className="space-y-4">
          <button
            onClick={() => router.push("/login")}
            className="w-full inline-flex items-center justify-between rounded-xl bg-blue-400 px-4 py-3 text-sm font-semibold text-white shadow-md hover:bg-blue-700 transition"
          >
            <div className="flex items-center gap-2">
              <span>관리자 로그인</span>
            </div>
            <span className="text-[11px] text-blue-100">
              약 데이터 등록 · 수정
            </span>
          </button>

          <button
            onClick={() => router.push("/pharmacy")}
            className="w-full inline-flex items-center justify-between rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm font-semibold text-gray-900 hover:bg-gray-50 transition"
          >
            <div className="flex items-center gap-2">
              <span>약사 화면 열기</span>
            </div>
            <span className="text-[11px] text-gray-400">
              검색 · 출력 생성
            </span>
          </button>
        </section>

        <footer className="mt-8 flex items-center justify-between text-[11px] text-gray-400">
          <span>© 2026 Drug Label Project</span>
        </footer>
      </div>
    </main>
  );
}