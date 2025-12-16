"use client";

import React, { useState } from "react";

import DomainForm from "./components/DomainForm";
import Overview from "./components/Overview";
import TopReferrers from "./components/TopReferrers";
import AnchorTexts from "./components/AnchorTexts";

export default function BacklinksPage() {
  const [domain, setDomain] = useState("");
  const [analysis, setAnalysis] = useState<any | null>(null);
  const [topReferrers, setTopReferrers] = useState<any[]>([]);
  const [anchorTexts, setAnchorTexts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyze(domainToAnalyze: string) {
    setError("");
    setLoading(true);
    try {
      const res = await fetch("/api/backlinks/analyze/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain: domainToAnalyze }),
      });
      const json = await res.json();
      if (json.ok) {
        setAnalysis(json.data);
      } else {
        setError(json.error || "API error");
      }
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }

  async function fetchReferrers(domainToFetch: string) {
    setError("");
    setLoading(true);
    try {
      const res = await fetch("/api/backlinks/top-referrers/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain: domainToFetch, limit: 20 }),
      });
      const json = await res.json();
      if (json.ok) setTopReferrers(json.top_referrers || []);
      else setError(json.error || "API error");
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }

  async function fetchAnchors(domainToFetch: string) {
    setError("");
    setLoading(true);
    try {
      const res = await fetch("/api/backlinks/anchor-texts/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain: domainToFetch, limit: 20 }),
      });
      const json = await res.json();
      if (json.ok) setAnchorTexts(json.anchor_texts || []);
      else setError(json.error || "API error");
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ padding: 24 }}>
      <h1>Backlink Analysis</h1>
      <DomainForm
        domain={domain}
        setDomain={setDomain}
        onAnalyze={() => analyze(domain)}
        onReferrers={() => fetchReferrers(domain)}
        onAnchors={() => fetchAnchors(domain)}
        loading={loading}
      />

      {error && <div style={{ color: "red" }}>{error}</div>}

      {analysis && <Overview analysis={analysis} />}

      {topReferrers.length > 0 && (
        <section style={{ marginTop: 24 }}>
          <h2>Top Referrers</h2>
          <TopReferrers data={topReferrers} />
        </section>
      )}

      {anchorTexts.length > 0 && (
        <section style={{ marginTop: 24 }}>
          <h2>Anchor Texts</h2>
          <AnchorTexts data={anchorTexts} />
        </section>
      )}
    </main>
  );
}
