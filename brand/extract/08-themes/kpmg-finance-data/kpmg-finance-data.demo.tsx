// Live preview for the KPMG Finance Data recipe (kpmg-finance-data.recipe.md).
// Numbers and charts: Cobalt cover led by three headline figures, white data pages with tables and bars.
import React from "react";
import { C, FONT, KpmgLogo, Slide, display, asset, CoverFooter, PageFooter, ThemeMeta } from "../_shared/kpmg";

export const theme: ThemeMeta = {
  id: "kpmg-finance-data",
  name: "KPMG Finance Data",
  mode: "light",
  tagline: "Numbers and charts",
  sources: "from KPMG China Hong Kong Banking Outlook 2026 + KPMG Denmark Annual Report",
  palette: [
    { name: "KPMG Blue", hex: C.blue, role: "Latest year, text" },
    { name: "Cobalt", hex: C.cobalt, role: "Primary series" },
    { name: "Pacific Blue", hex: C.pacific, role: "Comparison series" },
    { name: "Blue Tint 20", hex: C.tint20, role: "Highlighted column" },
    { name: "Grey 10", hex: C.grey10, role: "Gridlines, borders" },
  ],
};

// Sample data for layout only.
const years = ["2021/22", "2022/23", "2023/24", "2024/25", "2025/26"];
const revenue = [1342, 1465, 1594, 1588, 1712];
const rows: [string, ...number[]][] = [
  ["Net interest income", 412, 455, 498, 521, 547],
  ["Fee income", 233, 241, 262, 270, 289],
  ["Operating costs", -301, -318, -336, -342, -351],
  ["Profit before tax", 344, 378, 424, 449, 485],
  ["Cost / income ratio", 0.47, 0.46, 0.44, 0.43, 0.42],
];

const coverBg = `linear-gradient(180deg, ${C.cobalt} 0%, #1638B8 100%)`;

export function Cover({ width = 1280 }: { width?: number }) {
  const stats = [
    ["$15.2B", "sector profit after tax"],
    ["$2.3T", "total customer deposits"],
    ["0.72", "average loan-to-deposit ratio"],
  ];
  return (
    <Slide width={width} background={coverBg}>
      <img
        src={asset("04-photos/08-finance-and-banking/hk-banking-outlook-2026_p01_002.jpg")}
        style={{ position: "absolute", inset: 0, width: 1280, height: 720, objectFit: "cover", objectPosition: "70% 50%" }}
      />
      <div style={{ position: "absolute", inset: 0, background: "linear-gradient(90deg, rgba(30,73,226,0.92) 0%, rgba(30,73,226,0.6) 50%, transparent 80%)" }} />
      <div style={{ position: "absolute", left: 64, top: 56 }}>
        <KpmgLogo />
      </div>
      <div style={{ position: "absolute", left: 64, top: 190 }}>
        <div style={{ color: C.paleBlue, fontWeight: 700, fontSize: 15, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 22 }}>
          Financial services · Sector report 2026
        </div>
        <h1 style={display(96, C.white)}>Banking and</h1>
        <h1 style={display(96, C.white)}>capital markets</h1>
        <div style={{ display: "flex", gap: 64, marginTop: 52 }}>
          {stats.map(([v, l]) => (
            <div key={v} style={{ borderTop: `3px solid ${C.pacific}`, paddingTop: 12, width: 200 }}>
              <div style={display(54, C.white)}>{v}</div>
              <div style={{ color: C.paleBlue, fontSize: 14, marginTop: 6 }}>{l}</div>
            </div>
          ))}
        </div>
      </div>
      <CoverFooter right="Sample figures" />
    </Slide>
  );
}

function Bars() {
  const max = 2000;
  return (
    <svg width={480} height={300} style={{ overflow: "visible" }}>
      {[0, 500, 1000, 1500, 2000].map((g) => (
        <g key={g}>
          <line x1={44} x2={480} y1={260 - (g / max) * 240} y2={260 - (g / max) * 240} stroke={C.grey10} />
          <text x={36} y={264 - (g / max) * 240} textAnchor="end" fontSize={11} fill={C.grey60}>
            {g}
          </text>
        </g>
      ))}
      {revenue.map((v, i) => {
        const h = (v / max) * 240;
        const last = i === revenue.length - 1;
        return (
          <g key={i}>
            <rect x={70 + i * 82} y={260 - h} width={46} height={h} fill={last ? C.blue : C.pacific} />
            <text x={93 + i * 82} y={252 - h} textAnchor="middle" fontSize={12} fontWeight={700} fill={C.blue}>
              {v.toLocaleString()}
            </text>
            <text x={93 + i * 82} y={280} textAnchor="middle" fontSize={11} fill={C.blue}>
              {years[i]}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

const fmt = (n: number) => (Math.abs(n) < 1 ? n.toFixed(2) : n.toLocaleString());

export function Content({ width = 1280 }: { width?: number }) {
  return (
    <Slide width={width} background={C.white}>
      {/* Photo header strip with section tabs, as on every Hong Kong Banking Outlook content page */}
      <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: 56, background: `linear-gradient(rgba(30,73,226,0.55), rgba(0,51,141,0.7)), url(${asset("04-photos/08-finance-and-banking/hk-banking-outlook-2026_p03_007.jpg")}) center 30%/cover` }}>
        <div style={{ display: "flex", height: 6 }}>
          <span style={{ flex: 1, background: C.pacific }} />
          <span style={{ flex: 1, background: C.purple }} />
          <span style={{ flex: 1, background: C.lightBlue }} />
        </div>
      </div>
      <div style={{ position: "absolute", left: 64, top: 84, right: 64 }}>
        <h2 style={display(44, C.cobalt)}>Financial highlights</h2>
        <div style={{ display: "grid", gridTemplateColumns: "520px 1fr", gap: 28, marginTop: 20 }}>
          <div style={{ background: C.tint5, border: `1px solid ${C.tint20}`, padding: "18px 20px" }}>
            <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 14 }}>Revenue, USD m</div>
            <Bars />
          </div>
          <div style={{ background: C.tint5, border: `1px solid ${C.tint20}`, padding: "18px 20px" }}>
            <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 10 }}>Key figures, USD m</div>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, color: C.blue }}>
              <thead>
                <tr>
                  <th style={{ textAlign: "left", padding: "6px 4px", borderBottom: `1.5px solid ${C.blue}` }} />
                  {years.map((y, i) => (
                    <th key={y} style={{ textAlign: "right", padding: "6px 6px", borderBottom: `1.5px solid ${C.blue}`, background: i === 4 ? C.tint20 : undefined }}>
                      {y}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map(([label, ...vals]) => (
                  <tr key={label}>
                    <td style={{ padding: "9px 4px", borderBottom: `1px solid ${C.grey10}`, fontWeight: label.startsWith("Profit") ? 700 : 400 }}>{label}</td>
                    {vals.map((v, i) => (
                      <td key={i} style={{ textAlign: "right", padding: "9px 6px", borderBottom: `1px solid ${C.grey10}`, background: i === 4 ? C.tint20 : undefined, fontWeight: i === 4 ? 700 : 400 }}>
                        {fmt(v)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{ display: "flex", gap: 14, marginTop: 22 }}>
              {[
                ["+7.8%", "revenue growth"],
                ["0.42", "cost / income"],
                ["14.1%", "CET1 ratio"],
              ].map(([v, l]) => (
                <div key={l} style={{ flex: 1, background: C.white, borderTop: `3px solid ${C.cobalt}`, padding: "10px 12px" }}>
                  <div style={display(30, C.cobalt)}>{v}</div>
                  <div style={{ fontSize: 12, color: C.grey60, marginTop: 4 }}>{l}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div style={{ fontSize: 11, color: C.grey60, marginTop: 12 }}>Sample figures for layout only. Source line goes here, set in Grey 60.</div>
      </div>
      <PageFooter title="KPMG Finance Data theme" page={7} />
    </Slide>
  );
}

export default function Demo() {
  return (
    <div style={{ display: "grid", gap: 24, fontFamily: FONT.body }}>
      <Cover width={960} />
      <Content width={960} />
    </div>
  );
}
