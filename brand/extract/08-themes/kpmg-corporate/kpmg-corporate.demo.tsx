// Live preview for the KPMG Corporate recipe (kpmg-corporate.recipe.md).
// Light, everyday KPMG look: Cobalt cover, white editorial pages, KPMG Blue text.
import React from "react";
import { C, FONT, KpmgLogo, Slide, display, asset, CoverFooter, PageFooter, ThemeMeta } from "../_shared/kpmg";

export const theme: ThemeMeta = {
  id: "kpmg-corporate",
  name: "KPMG Corporate",
  mode: "light",
  tagline: "The everyday KPMG look",
  sources: "from all 5 library reports + KPMG Global tech report 2026",
  palette: [
    { name: "KPMG Blue", hex: C.blue, role: "Text, headlines" },
    { name: "Cobalt", hex: C.cobalt, role: "Covers, section pages" },
    { name: "Pacific Blue", hex: C.pacific, role: "Accent words, numbers" },
    { name: "Blue Tint 10", hex: C.tint10, role: "Panels" },
    { name: "White", hex: C.white, role: "Page" },
  ],
};

const coverBg = `linear-gradient(115deg, ${C.cobalt} 0%, #1A3FD0 45%, ${C.blue} 100%)`;

/** Semicircle gauge, the dial style from the tech report's maturity figures. */
function Gauge({ value, label, size = 120 }: { value: number; label: string; size?: number }) {
  const r = size / 2 - 10;
  const len = Math.PI * r;
  return (
    <div style={{ textAlign: "center", width: size }}>
      <svg width={size} height={size / 2 + 10}>
        <path d={`M10 ${size / 2} A${r} ${r} 0 0 1 ${size - 10} ${size / 2}`} fill="none" stroke={C.tint20} strokeWidth={12} />
        <path
          d={`M10 ${size / 2} A${r} ${r} 0 0 1 ${size - 10} ${size / 2}`}
          fill="none"
          stroke={C.cobalt}
          strokeWidth={12}
          strokeDasharray={`${(len * value) / 100} ${len}`}
        />
      </svg>
      <div style={display(34, C.blue, { marginTop: -6 })}>{value}%</div>
      <div style={{ fontSize: 13, color: C.grey60, marginTop: 4 }}>{label}</div>
    </div>
  );
}

export function Cover({ width = 1280 }: { width?: number }) {
  return (
    <Slide width={width} background={coverBg}>
      <img
        src={asset("04-photos/04-technology-and-abstract/global-tech-report-2026_p20_06.jpg")}
        style={{ position: "absolute", right: 0, top: 0, width: 640, height: 720, objectFit: "cover", objectPosition: "35% 50%", mixBlendMode: "screen", opacity: 0.9, maskImage: "linear-gradient(90deg, transparent 0%, #000 35%)", WebkitMaskImage: "linear-gradient(90deg, transparent 0%, #000 35%)" }}
      />
      <div style={{ position: "absolute", left: 64, top: 56 }}>
        <KpmgLogo />
      </div>
      <div style={{ position: "absolute", left: 64, top: 200 }}>
        <h1 style={display(104, C.white)}>KPMG Global</h1>
        <h1 style={display(104, C.paleBlue, { paddingLeft: 72 })}>theme preview</h1>
        <div style={{ display: "flex", alignItems: "flex-end", gap: 20, paddingLeft: 72 }}>
          <h1 style={display(104, C.paleBlue)}>2026</h1>
          <p style={{ color: C.white, fontSize: 19, lineHeight: 1.3, margin: "0 0 14px", maxWidth: 330 }}>
            Measured from the 2026 KPMG publications in the asset library
          </p>
        </div>
      </div>
      <CoverFooter right="kpmg.com" />
    </Slide>
  );
}

export function Content({ width = 1280 }: { width?: number }) {
  return (
    <Slide width={width} background={C.white}>
      <div style={{ position: "absolute", left: 64, top: 52, right: 64 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 14, fontWeight: 700, color: C.cobalt }}>
          <span style={{ width: 12, height: 12, background: C.cobalt, display: "inline-block" }} /> Local, regional, global
        </div>
        <h2 style={display(52, C.blue, { marginTop: 14 })}>Where organisations invest in 2026</h2>
        <div style={{ display: "grid", gridTemplateColumns: "1.1fr 1fr", gap: 56, marginTop: 36 }}>
          <div style={{ fontSize: 17, lineHeight: 1.5, color: C.blue }}>
            <p style={{ marginTop: 0 }}>
              Body copy is set in KPMG Blue, not black, left-aligned on a white page with generous margins. Use one idea per column
              and let the <b>bold lead-in</b> carry the number.
            </p>
            <p style={{ color: C.grey60 }}>Secondary text and captions drop to Grey 60.</p>
            <div style={{ background: C.tint10, padding: "20px 24px", borderLeft: `4px solid ${C.pacific}`, marginTop: 24 }}>
              <div style={display(44, C.cobalt)}>42%</div>
              <div style={{ fontSize: 15, marginTop: 6 }}>of the budget goes to growth initiatives (sample figure)</div>
            </div>
          </div>
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0 24px" }}>
              <Gauge value={38} label="Local" />
              <Gauge value={35} label="Regional" />
              <Gauge value={32} label="Global" />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
              {["Address tech debt", "Keep cost discipline"].map((t) => (
                <div key={t} style={{ background: `linear-gradient(90deg, ${C.pacific}, ${C.paleBlue})`, padding: "18px 18px 26px" }}>
                  <div style={display(26, C.blue)}>{t}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      <PageFooter title="KPMG Corporate theme" page={4} />
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
