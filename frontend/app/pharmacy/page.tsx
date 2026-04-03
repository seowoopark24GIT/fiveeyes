"use client";

import { FormEvent, useState } from "react";

type Medicine = {
  id: number;
  name: string;
  description?: string | null;
  dosage: string;
  caution: string;
};

export default function PharmacyPage() {
  const [keyword, setKeyword] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [dosage, setDosage] = useState("");
  const [caution, setCaution] = useState("");
  const [nfcData, setNfcData] = useState("");
  const [brailleName, setBrailleName] = useState("");
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [loadingGenerate, setLoadingGenerate] = useState(false);

  async function handleSearch(e: FormEvent) {
    e.preventDefault();
    if (!keyword.trim()) return;

    setLoadingSearch(true);

    try {
      const res = await fetch(
        `http://127.0.0.1:8000/medicines/search?name=${encodeURIComponent(
          keyword,
        )}`,
      );

      if (!res.ok) {
        alert("검색 실패 (서버 오류)");
        return;
      }

      const data: Medicine[] = await res.json();

      if (!data || data.length === 0) {
        alert("DB에 없는 약입니다. 직접 입력하세요.");
        return;
      }

      const med = data[0];
      setName(med.name ?? "");
      setDescription(med.description ?? "");
      setDosage(med.dosage ?? "");
      setCaution(med.caution ?? "");
    } catch (err) {
      console.error(err);
      alert("검색 중 오류가 발생했습니다.");
    } finally {
      setLoadingSearch(false);
    }
  }

  async function handleGenerate(e: FormEvent) {
    e.preventDefault();
    setLoadingGenerate(true);
    setNfcData("");
    setBrailleName("");

    try {
      const res = await fetch("http://127.0.0.1:8000/pharmacy/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          description,
          dosage,
          caution,
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        alert("에러 발생: " + text);
        return;
      }

      const data = await res.json();
      setNfcData(data.nfc_data);
      setBrailleName(data.braille_name);
    } catch (err) {
      console.error(err);
      alert("출력 생성 중 오류가 발생했습니다.");
    } finally {
      setLoadingGenerate(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <h1 className="text-lg font-semibold text-gray-900">
            Pharmacy Drug Label Output
          </h1>
          <a
            href="/"
            className="text-xs text-gray-500 hover:text-gray-700 underline"
          >
            홈으로
          </a>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-6 py-8 space-y-6">
        {/* 1. 검색 */}
        <section className="rounded-2xl bg-white p-6 shadow-sm border border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">
            1. 약 검색
          </h2>
          <form
            onSubmit={handleSearch}
            className="mt-4 flex flex-col gap-3 sm:flex-row"
          >
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="약 이름 입력"
              className="flex-1 rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <button
              type="submit"
              disabled={loadingSearch}
              className="inline-flex items-center justify-center rounded-xl bg-blue-400 px-4 py-2 text-sm font-semibold text-white shadow-md hover:bg-blue-700 disabled:opacity-60"
            >
              {loadingSearch ? "검색 중..." : "검색"}
            </button>
          </form>
        </section>

        {/* 2. 정보 수정 + 출력 생성 */}
        <section className="rounded-2xl bg-white p-6 shadow-sm border border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">
            2. 약 정보 입력 · 수정
          </h2>

          <form onSubmit={handleGenerate} className="mt-4 space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                약 이름
              </label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                한 줄 설명
              </label>
              <input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                복용방법
              </label>
              <textarea
                rows={3}
                value={dosage}
                onChange={(e) => setDosage(e.target.value)}
                className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                주의사항
              </label>
              <textarea
                rows={3}
                value={caution}
                onChange={(e) => setCaution(e.target.value)}
                className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <button
              type="submit"
              disabled={loadingGenerate}
              className="mt-2 w-full inline-flex items-center justify-center rounded-xl bg-blue-400 px-4 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-blue-700 disabled:opacity-60"
            >
              {loadingGenerate ? "생성 중..." : "출력 생성"}
            </button>
          </form>
        </section>

        {/* 3. 결과 */}
        <section className="rounded-2xl bg-white p-6 shadow-sm border border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">
            3. 출력 결과
          </h2>

          <div className="mt-4 space-y-4">
            <div className="rounded-xl bg-gray-50 p-4">
              <strong className="text-xs text-gray-700">
                NFC 저장 정보
              </strong>
              <pre className="mt-2 text-xs text-gray-800 whitespace-pre-wrap">
                {nfcData || "아직 생성된 정보가 없습니다."}
              </pre>
            </div>

            <div className="rounded-xl bg-gray-50 p-4">
              <strong className="text-xs text-gray-700">
                점자 약 이름
              </strong>
              <div className="mt-2 text-xs text-gray-900">
                {brailleName || "아직 생성된 정보가 없습니다."}
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}