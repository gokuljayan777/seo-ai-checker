import React from "react";

export default function Overview({ analysis }: any) {
  return (
    <section style={{ marginTop: 24 }}>
      <h2>Overview for {analysis.domain}</h2>
      <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
        <div style={{ minWidth: 160 }}>
          <strong>Total Backlinks</strong>
          <div>{analysis.total_backlinks}</div>
        </div>
        <div style={{ minWidth: 160 }}>
          <strong>Referring Domains</strong>
          <div>{analysis.referring_domains}</div>
        </div>
        <div style={{ minWidth: 160 }}>
          <strong>Toxic Score</strong>
          <div>{analysis.toxic_score}</div>
        </div>
      </div>
    </section>
  );
}
