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
  score?: number;
  score_breakdown?: [string, number, string[]][];
  rule_issues?: string[];
  raw_html_snippet?: string;
  llm_suggestions?: {
    improved_title?: string;
    improved_meta_description?: string;
    improved_h1?: string;
    seo_summary?: string;
    suggestions?: string[];
    error?: string;
    ok?: boolean;
  };
  llm_generated_at?: string;
  // Sitemap crawl results
  ok?: boolean;
  base_url?: string;
  sitemaps_found?: string[];
  pages_analyzed?: number;
  pages_failed?: number;
  pages?: Array<{
    url: string;
    status: string;
    status_code?: number;
    score?: number;
    title?: string;
    issues_count?: number;
    error?: string;
  }>;
  analyzed_at?: string;
  error?: string;
};

export default function Home() {
  const [url, setUrl] = useState("");
  const [crawlSite, setCrawlSite] = useState(false);
  const [resp, setResp] = useState<ApiResult | null>(null);
  const [loading, setLoading] = useState(false);

  const analyze = async () => {
    if (!url) return alert("Please enter a URL");

    setLoading(true);
    setResp(null);

    try {
      const r = await axios.post("/api/analyze", { url, crawl_site: crawlSite });
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

        <div className="flex items-center gap-3 mb-3">
          <input
            type="checkbox"
            id="crawlSite"
            checked={crawlSite}
            onChange={(e) => setCrawlSite(e.target.checked)}
            className="w-4 h-4"
          />
          <label htmlFor="crawlSite" className="text-black cursor-pointer">
            Analyze entire site (via sitemap)
          </label>
        </div>

        <button
          onClick={analyze}
          disabled={loading}
          className="w-full bg-blue-600 text-white py-3 rounded hover:bg-blue-700 transition disabled:bg-blue-300"
        >
          {loading ? "Analyzing..." : crawlSite ? "Analyze Site" : "Analyze"}
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

          {/* Sitemap crawl results */}
          {resp && resp.ok && resp.pages && (
            <div className="space-y-4 text-black">
              <div className="p-4 border-2 border-purple-500 rounded bg-purple-50">
                <h2 className="font-bold text-purple-900 mb-3">
                  📊 Site Analysis Report
                </h2>
                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div>
                    <div className="text-xs text-purple-600">Pages Analyzed</div>
                    <div className="text-2xl font-bold text-purple-900">
                      {resp.pages_analyzed}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-red-600">Failed</div>
                    <div className="text-2xl font-bold text-red-900">
                      {resp.pages_failed || 0}
                    </div>
                  </div>
                </div>
                {resp.sitemaps_found && resp.sitemaps_found.length > 0 && (
                  <div className="text-xs text-purple-700 mb-2">
                    Found {resp.sitemaps_found.length} sitemap(s)
                  </div>
                )}
              </div>

              {/* Pages list */}
              <div className="p-3 border rounded">
                <h3 className="font-bold text-black mb-2">Pages</h3>
                <div className="max-h-96 overflow-y-auto space-y-2">
                  {resp.pages.map((p, i) => (
                    <div
                      key={i}
                      className={`p-2 rounded text-xs border ${
                        p.status === "success"
                          ? "bg-green-50 border-green-200"
                          : "bg-red-50 border-red-200"
                      }`}
                    >
                      <div className="font-semibold text-black truncate">
                        {p.title || p.url}
                      </div>
                      <div className="text-gray-600 truncate text-xs">
                        {p.url}
                      </div>
                      {p.status === "success" && (
                        <div className="flex gap-2 mt-1 text-black">
                          <span>Score: {p.score}/100</span>
                          {p.issues_count && p.issues_count > 0 && (
                            <span className="text-red-600">
                              Issues: {p.issues_count}
                            </span>
                          )}
                        </div>
                      )}
                      {p.status === "error" && (
                        <div className="text-red-600 text-xs mt-1">
                          {p.error}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Single page results */}
          {resp && !resp.error && !resp.pages && (
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

              {resp.llm_suggestions && !resp.llm_suggestions.error && (
                <div className="p-4 border-2 border-green-500 rounded bg-green-50">
                  <h3 className="font-bold text-green-900 mb-3">
                    🤖 AI SEO Suggestions
                  </h3>
                  
                  {resp.llm_suggestions.seo_summary && (
                    <div className="mb-3 p-2 bg-white rounded border border-green-200">
                      <h4 className="font-semibold text-black text-sm">Summary</h4>
                      <p className="text-sm text-black mt-1">
                        {resp.llm_suggestions.seo_summary}
                      </p>
                    </div>
                  )}

                  {resp.llm_suggestions.improved_title && (
                    <div className="mb-3 p-2 bg-white rounded border border-green-200">
                      <h4 className="font-semibold text-black text-sm">
                        Improved Title
                      </h4>
                      <p className="text-sm text-blue-600 mt-1">
                        {resp.llm_suggestions.improved_title}
                      </p>
                    </div>
                  )}

                  {resp.llm_suggestions.improved_meta_description && (
                    <div className="mb-3 p-2 bg-white rounded border border-green-200">
                      <h4 className="font-semibold text-black text-sm">
                        Improved Meta Description
                      </h4>
                      <p className="text-sm text-blue-600 mt-1">
                        {resp.llm_suggestions.improved_meta_description}
                      </p>
                    </div>
                  )}

                  {resp.llm_suggestions.improved_h1 && (
                    <div className="mb-3 p-2 bg-white rounded border border-green-200">
                      <h4 className="font-semibold text-black text-sm">
                        Improved H1
                      </h4>
                      <p className="text-sm text-blue-600 mt-1">
                        {resp.llm_suggestions.improved_h1}
                      </p>
                    </div>
                  )}

                  {resp.llm_suggestions.suggestions &&
                    resp.llm_suggestions.suggestions.length > 0 && (
                      <div className="p-2 bg-white rounded border border-green-200">
                        <h4 className="font-semibold text-black text-sm mb-2">
                          Quick Tips
                        </h4>
                        <ul className="list-disc pl-5 text-sm text-black space-y-1">
                          {resp.llm_suggestions.suggestions.map((s, i) => (
                            <li key={i}>{s}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                  {resp.llm_generated_at && (
                    <div className="text-xs text-gray-500 mt-2">
                      Generated: {new Date(resp.llm_generated_at).toLocaleString()}
                    </div>
                  )}
                </div>
              )}

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
