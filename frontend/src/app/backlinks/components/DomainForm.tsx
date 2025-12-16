import React from "react";

export default function DomainForm({
  domain,
  setDomain,
  onAnalyze,
  onReferrers,
  onAnchors,
  loading,
}: any) {
  return (
    <div style={{ display: "flex", gap: 12, alignItems: "center", marginTop: 16 }}>
      <input
        aria-label="domain"
        placeholder="example.com"
        value={domain}
        onChange={(e) => setDomain(e.target.value)}
        style={{ padding: 8, minWidth: 300 }}
      />
      <button onClick={onAnalyze} disabled={loading || !domain}>
        Analyze
      </button>
      <button onClick={onReferrers} disabled={loading || !domain}>
        Referrers
      </button>
      <button onClick={onAnchors} disabled={loading || !domain}>
        Anchors
      </button>
    </div>
  );
}
