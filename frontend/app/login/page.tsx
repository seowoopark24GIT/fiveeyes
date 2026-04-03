"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("1234");
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");

    try {
      const formData = new FormData();
      formData.append("username", username);
      formData.append("password", password);

      const res = await fetch("http://127.0.0.1:8000/auth/login", {
        method: "POST",
        body: formData,
        credentials: "include", // 세션 쿠키 사용
      });

      if (res.redirected) {
        router.push("/admin");
        return;
      }

      if (!res.ok) {
        setError("로그인에 실패했습니다.");
        return;
      }

      router.push("/admin");
    } catch (err) {
      console.error(err);
      setError("로그인 중 오류가 발생했습니다.");
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md bg-white shadow-xl rounded-2xl px-8 py-10">
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">
          관리자 로그인
        </h1>
        <p className="mt-2 text-sm text-gray-500">
          약품 정보 관리를 위한 관리자 전용 페이지입니다.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              아이디
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="admin"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              비밀번호
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="비밀번호를 입력하세요"
              required
            />
          </div>

          {error && (
            <p className="text-xs text-red-600 mt-1">{error}</p>
          )}

          <button
            type="submit"
            className="w-full inline-flex items-center justify-center rounded-xl bg-blue-400 px-4 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-blue-700 transition"
          >
            로그인
          </button>
        </form>

        <button
          onClick={() => router.push("/")}
          className="mt-4 text-xs text-gray-500 hover:text-gray-700 underline"
        >
          홈으로 돌아가기
        </button>
      </div>
    </main>
  );
}