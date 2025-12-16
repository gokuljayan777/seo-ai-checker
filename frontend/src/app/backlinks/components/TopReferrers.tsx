import React from "react";

export default function TopReferrers({ data }: any) {
  return (
    <table style={{ borderCollapse: "collapse", width: "100%" }}>
      <thead>
        <tr>
          <th style={{ textAlign: "left", padding: 8 }}>Referrer</th>
          <th style={{ textAlign: "left", padding: 8 }}>Estimated Links</th>
        </tr>
      </thead>
      <tbody>
        {data.map((r: any, i: number) => (
          <tr key={i}>
            <td style={{ padding: 8 }}>{r.referrer}</td>
            <td style={{ padding: 8 }}>{r.estimated_links}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
