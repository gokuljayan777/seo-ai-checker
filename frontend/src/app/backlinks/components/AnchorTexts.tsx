import React from "react";

export default function AnchorTexts({ data }: any) {
  return (
    <div>
      <ul>
        {data.map((a: any, i: number) => (
          <li key={i}>
            {a[0]} <strong>({a[1]})</strong>
          </li>
        ))}
      </ul>
    </div>
  );
}
