"use client";

import { useEffect, useState } from "react";

type Medicine = {
  id: number;
  name: string;
  description?: string | null;
  dosage: string;
  caution: string;
};

export default function AdminPage() {
  const [keyword, setKeyword] = useState("");
  const [results, setResults] = useState<Medicine[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);

  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newDosage, setNewDosage] = useState("");
  const [newCaution, setNewCaution] = useState("");

  async function fetchSearch() {
    if (!keyword.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/medicines/search?name=${encodeURIComponent(
          keyword,
        )}`,
        { credentials: "include" },
      );
      if (!res.ok) {
        alert("검색 실패 (권한 또는 서버 문제)");
        return;
      }
      const data: Medicine[] = await res.json();
      setResults(data);
    } catch (e) {
      console.error(e);
      alert("검색 중 에러가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    if (!newName || !newDosage || !newCaution) {
      alert("이름, 복용방법, 주의사항은 필수입니다.");
      return;
    }
    setCreating(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/medicines", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          name: newName,
          description: newDesc,
          dosage: newDosage,
          caution: newCaution,
        }),
      });
      if (!res.ok) {
        alert("추가 실패");
        return;
      }
      setNewName("");
      setNewDesc("");
      setNewDosage("");
      setNewCaution("");
      // 방금 추가한 약도 검색 결과에서 보고 싶으면 다시 검색
      if (keyword.trim()) {
        await fetchSearch();
      }
    } catch (e) {
      console.error(e);
      alert("추가 중 에러가 발생했습니다.");
    } finally {
      setCreating(false);
    }
  }

  async function handleUpdate(med: Medicine) {
    if (!confirm("이 약 정보를 수정하시겠습니까?")) return;
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/medicines/${med.id}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            name: med.name,
            description: med.description ?? "",
            dosage: med.dosage,
            caution: med.caution,
          }),
        },
      );
      if (!res.ok) {
        alert("수정 실패 (권한 또는 서버 오류)");
        return;
      }
      alert("수정 완료");
      await fetchSearch();
    } catch (e) {
      console.error(e);
      alert("수정 중 에러가 발생했습니다.");
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("정말 삭제하시겠습니까? (복구 불가)")) return;
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/medicines/${id}`,
        {
          method: "DELETE",
          credentials: "include",
        },
      );
      if (!res.ok) {
        alert("삭제 실패 (권한 또는 서버 오류)");
        return;
      }
      alert("삭제 완료");
      setResults((prev) => prev.filter((m) => m.id !== id));
    } catch (e) {
      console.error(e);
      alert("삭제 중 에러가 발생했습니다.");
    }
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <h1 className="text-lg font-semibold text-gray-900">
            관리자 · 약품 관리
          </h1>
          <div className="space-x-3 text-xs">
            <a
              href="/"
              className="text-gray-500 hover:text-gray-700 underline"
            >
              홈
            </a>
            <a
              href="http://127.0.0.1:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="text-gray-500 hover:text-gray-700 underline"
            >
              API Docs
            </a>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-6 py-8 space-y-6">
        {/* 1. 약 추가 */}
        <section className="rounded-2xl bg-white p-6 shadow-sm border border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">
            1. 약 추가
          </h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="약 이름"
              className="rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <input
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              placeholder="한 줄 설명"
              className="rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <input
              value={newDosage}
              onChange={(e) => setNewDosage(e.target.value)}
              placeholder="복용방법"
              className="rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <input
              value={newCaution}
              onChange={(e) => setNewCaution(e.target.value)}
              placeholder="주의사항"
              className="rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <button
            onClick={handleCreate}
            disabled={creating}
            className="mt-4 inline-flex items-center justify-center rounded-xl bg-blue-400 px-4 py-2 text-sm font-semibold text-white shadow-md hover:bg-blue-700 disabled:opacity-60"
          >
            {creating ? "추가 중..." : "추가"}
          </button>
        </section>

        {/* 2. 검색 */}
        <section className="rounded-2xl bg-white p-6 shadow-sm border border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">
            2. 약 검색
          </h2>
          <div className="mt-4 flex flex-col gap-3 sm:flex-row">
            <input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="약 이름 입력"
              className="flex-1 rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <button
              onClick={fetchSearch}
              disabled={loading}
              className="inline-flex items-center justify-center rounded-xl bg-blue-400 px-4 py-2 text-sm font-semibold text-white shadow-md hover:bg-blue-700 disabled:opacity-60"
            >
              {loading ? "검색 중..." : "검색"}
            </button>
          </div>
        </section>

        {/* 3. 검색 결과 */}
        <section className="rounded-2xl bg-white p-6 shadow-sm border border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">
            3. 검색 결과
          </h2>
          <div className="mt-4 space-y-4">
            {results.length === 0 && (
              <p className="text-xs text-gray-400">
                검색 결과가 없습니다.
              </p>
            )}
            {results.map((med) => (
              <div
                key={med.id}
                className="rounded-xl border border-gray-200 bg-gray-50 p-4 space-y-2"
              >
                <div className="text-xs text-gray-500">ID: {med.id}</div>
                <input
                  value={med.name}
                  onChange={(e) =>
                    setResults((prev) =>
                      prev.map((m) =>
                        m.id === med.id
                          ? { ...m, name: e.target.value }
                          : m,
                      ),
                    )
                  }
                  className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm mb-1"
                />
                <input
                  value={med.description ?? ""}
                  onChange={(e) =>
                    setResults((prev) =>
                      prev.map((m) =>
                        m.id === med.id
                          ? { ...m, description: e.target.value }
                          : m,
                      ),
                    )
                  }
                  className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm mb-1"
                />
                <input
                  value={med.dosage}
                  onChange={(e) =>
                    setResults((prev) =>
                      prev.map((m) =>
                        m.id === med.id
                          ? { ...m, dosage: e.target.value }
                          : m,
                      ),
                    )
                  }
                  className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm mb-1"
                />
                <input
                  value={med.caution}
                  onChange={(e) =>
                    setResults((prev) =>
                      prev.map((m) =>
                        m.id === med.id
                          ? { ...m, caution: e.target.value }
                          : m,
                      ),
                    )
                  }
                  className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm mb-3"
                />

                <div className="flex gap-2">
                  <button
                    onClick={() => handleUpdate(med)}
                    className="inline-flex items-center justify-center rounded-full bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-700"
                  >
                    수정
                  </button>
                  <button
                    onClick={() => handleDelete(med.id)}
                    className="inline-flex items-center justify-center rounded-full bg-red-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-700"
                  >
                    삭제
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}