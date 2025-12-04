"use client";

import { useState } from "react";
import axios from "axios";

type ApiResult = {
  url?: string;
  status_code?: number;
  title?: string;
  meta_description?: string;
  h1?: string[] | string;
  h2?: string[];
  h3?: string[];
  word_count?: number;
  images?: { src?: string; alt?: string }[];
  issues?: { code?: string; message?: string }[];
  raw_html_snippet?: string;
  error?: string;
};

export default function Home() {
  const [url, setUrl] = useState("");
  const [resp, setResp] = useState<ApiResult | null>(null);
  const [loading, setLoading] = useState(false);

  const analyze = async () => {
    if (!url) return alert("Please enter a URL");

    setLoading(true);
    setResp(null);

    try {
      const r = await axios.post("/api/analyze", { url });
      setResp(r.data);
    } catch (err: any) {
      console.error(err);
      setResp({ error: err?.message || "Failed to connect to backend" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-8">
      <main className="w-full max-w-xl bg-white p-6 rounded-xl shadow text-black">
        <h1 className="text-2xl font-bold mb-4 text-center text-black">
          🔍 SEO AI Checker
        </h1>

        <input
          type="text"
          placeholder="Enter website URL (include https://)"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="w-full p-3 border rounded mb-3 text-black placeholder-black"
        />

        <button
          onClick={analyze}
          disabled={loading}
          className="w-full bg-blue-600 text-white py-3 rounded hover:bg-blue-700 transition disabled:bg-blue-300"
        >
          {loading ? "Analyzing..." : "Analyze"}
        </button>

        <div className="mt-6 text-black">
          {!resp && !loading && (
            <div className="text-sm text-black">No result yet.</div>
          )}

          {resp?.error && (
            <div className="bg-red-100 text-red-800 p-3 rounded">
              Error: {resp.error}
            </div>
          )}

          {resp && !resp.error && (
            <div className="space-y-4 text-black">
              <div className="p-4 border rounded bg-black text-white">
                <div className="text-sm">Status: {resp.status_code}</div>
                <div className="text-lg font-semibold mt-1">
                  {resp.title || "(no title)"}
                </div>
                <div className="text-xs text-white mt-1">{resp.url}</div>
              </div>

              <div className="p-4 border rounded">
                <h3 className="font-medium text-black">Meta description</h3>
                <p className="text-xs text-black mt-1">
                  {resp.meta_description || <em>(missing)</em>}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 border rounded">
                  <h4 className="font-medium text-black">H1</h4>
                  <ul className="list-disc pl-5 text-sm text-black">
                    {(Array.isArray(resp.h1) ? resp.h1 : [resp.h1]).map(
                      (h, i) => (h ? <li key={i}>{h}</li> : null)
                    )}
                  </ul>
                </div>

                <div className="p-3 border rounded">
                  <h4 className="font-medium text-black">Word count</h4>
                  <div className="text-sm text-black">
                    {resp.word_count ?? 0}
                  </div>
                </div>
              </div>

              <div className="p-3 border rounded">
                <h4 className="font-medium text-black">Detected issues</h4>
                {resp.issues && resp.issues.length ? (
                  <ul className="list-disc pl-5 text-sm text-red-700">
                    {resp.issues.map((it, i) => (
                      <li key={i} className="text-black">
                        <strong className="text-black">{it.code}</strong>:{" "}
                        <span className="text-black">{it.message}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-sm text-green-700">No issues found</div>
                )}
              </div>

              <details className="p-3 border rounded text-black">
                <summary className="cursor-pointer font-medium text-black">
                  Raw HTML snippet (first 8KB)
                </summary>
                <pre className="mt-2 whitespace-pre-wrap text-xs bg-gray-900 text-white p-2 rounded">
                  {resp.raw_html_snippet}
                </pre>
              </details>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
