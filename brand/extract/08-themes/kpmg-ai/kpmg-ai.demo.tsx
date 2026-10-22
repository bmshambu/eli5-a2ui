// Live preview for the KPMG AI recipe (kpmg-ai.recipe.md).
// Dark and glowing, for AI topics: navy-to-cobalt night sky, neon light imagery, glass panels.
import React from "react";
import { C, FONT, KpmgLogo, Slide, display, asset, CoverFooter, PageFooter, ThemeMeta } from "../_shared/kpmg";

export const theme: ThemeMeta = {
  id: "kpmg-ai",
  name: "KPMG AI",
  mode: "dark",
  tagline: "Glowing, for AI topics",
  sources: "from KPMG US AI Quarterly Pulse (Jan 2026) + Global tech report 2026",
  palette: [
    { name: "Ink Navy", hex: C.ink, role: "Page background" },
    { name: "Cobalt", hex: C.cobalt, role: "Glow, gradients" },
    { name: "Pacific Blue", hex: C.pacific, role: "Neon lines, numbers" },
    { name: "Purple", hex: C.purple, role: "Second glow" },
    { name: "Light Purple", hex: C.lightPurple, role: "Hero stat bubble" },
  ],
};

// The AI Pulse deck keeps pages blue, not black: neon photography sits under a Cobalt wash.
const nightBg = `radial-gradient(1200px 700px at 78% 30%, ${C.cobalt} 0%, #10239A 35%, ${C.ink} 75%)`;
const pageBg = `linear-gradient(rgba(16,40,190,0.78), rgba(12,30,150,0.86)), url(${asset("04-photos/07-ai-neon-backgrounds/ai-pulse-q4-2025_p04.jpg")}) center/cover`;
const glass: React.CSSProperties = {
  background: "linear-gradient(160deg, rgba(30,73,226,0.35), rgba(5,11,46,0.75))",
  border: `1px solid ${C.pacific}`,
  boxShadow: `0 0 24px rgba(0,184,245,0.45), inset 0 0 18px rgba(0,184,245,0.15)`,
  borderRadius: 6,
};

/** Glowing ring stat used on dark AI pages. */
function Ring({ value, label }: { value: number; label: string }) {
  const r = 46;
  const len = 2 * Math.PI * r;
  return (
    <div style={{ textAlign: "center" }}>
      <svg width={120} height={120} style={{ filter: `drop-shadow(0 0 8px ${C.pacific})` }}>
        <circle cx={60} cy={60} r={r} fill="none" stroke="rgba(172,234,255,0.15)" strokeWidth={8} />
        <circle cx={60} cy={60} r={r} fill="none" stroke="url(#ring)" strokeWidth={8} strokeLinecap="round" strokeDasharray={`${(len * value) / 100} ${len}`} transform="rotate(-90 60 60)" />
        <defs>
          <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor={C.pacific} />
            <stop offset="1" stopColor={C.lightPurple} />
          </linearGradient>
        </defs>
        <text x={60} y={68} textAnchor="middle" fill={C.white} style={{ fontFamily: FONT.display, fontWeight: 700, fontSize: 28 }}>
          {value}%
        </text>
      </svg>
      <div style={{ color: C.paleBlue, fontSize: 13, maxWidth: 150, margin: "4px auto 0", lineHeight: 1.3 }}>{label}</div>
    </div>
  );
}

export function Cover({ width = 1280 }: { width?: number }) {
  return (
    <Slide width={width} background={nightBg}>
      <img
        src={asset("04-photos/07-ai-neon-backgrounds/ai-pulse-q4-2025_p01.jpg")}
        style={{ position: "absolute", inset: 0, width: 1280, height: 720, objectFit: "cover" }}
      />
      <div style={{ position: "absolute", inset: 0, background: "linear-gradient(90deg, rgba(20,40,200,0.85) 0%, rgba(20,40,200,0.35) 45%, transparent 70%)" }} />
      <div style={{ position: "absolute", left: 64, top: 56 }}>
        <KpmgLogo />
      </div>
      <div style={{ position: "absolute", left: 64, top: 210 }}>
        <div style={{ color: C.pacific, fontWeight: 700, fontSize: 15, letterSpacing: "0.04em", marginBottom: 20 }}>Thought leadership · 2026</div>
        <h1 style={display(112, C.white, { textShadow: "0 0 30px rgba(0,184,245,0.35)" })}>Agentic AI</h1>
        <h1 style={display(112, C.pacific, { textShadow: "0 0 30px rgba(0,184,245,0.45)" })}>at scale</h1>
        <p style={{ color: C.paleBlue, fontSize: 20, lineHeight: 1.35, maxWidth: 420, marginTop: 26 }}>
          From pilots to orchestrated systems: what separates the AI leaders
        </p>
      </div>
      <CoverFooter />
    </Slide>
  );
}

export function Content({ width = 1280 }: { width?: number }) {
  return (
    <Slide width={width} background={pageBg} style={{ color: C.white }}>
      <div style={{ position: "absolute", left: 64, top: 52, right: 64 }}>
        <div style={{ color: C.pacific, fontSize: 14, fontWeight: 700 }}>Q4 2025 highlights</div>
        <h2 style={display(52, C.white, { marginTop: 12 })}>
          Agents move from <span style={{ background: `linear-gradient(90deg, ${C.pacific}, ${C.lightPurple})`, WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent" }}>pilots to production</span>
        </h2>
        <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr", gap: 32, marginTop: 34 }}>
          <div style={{ ...glass, padding: "28px 24px", display: "flex", justifyContent: "space-around", alignSelf: "start" }}>
            <Ring value={64} label="are piloting or deploying AI agents" />
            <Ring value={41} label="report measurable ROI from agents" />
            <Ring value={27} label="run agents across several functions" />
          </div>
          <div style={{ display: "grid", gap: 16, alignContent: "start" }}>
            {[
              [83, "implementation speed"],
              [69, "reliability"],
              [75, "security and compliance"],
            ].map(([v, t]) => (
              <div key={t}>
                <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
                  <span style={display(36, C.pacific)}>{v}%</span>
                  <span style={{ fontSize: 14, color: C.paleBlue }}>{t}</span>
                </div>
                <div style={{ height: 10, borderRadius: 5, background: "rgba(172,234,255,0.2)", marginTop: 6 }}>
                  <div style={{ width: `${v}%`, height: "100%", borderRadius: 5, background: C.pacific, boxShadow: `0 0 10px ${C.pacific}` }} />
                </div>
              </div>
            ))}
            <div style={{ fontWeight: 700, fontSize: 14, marginTop: 6 }}>Top challenges in deploying AI:</div>
            {["01.  Cybersecurity", "02.  Data privacy", "03.  Data quality"].map((t) => (
              <div key={t} style={{ background: C.pacific, color: C.blue, borderRadius: 20, padding: "7px 18px", fontWeight: 700, fontSize: 15 }}>
                {t}
              </div>
            ))}
          </div>
        </div>
        <div style={{ fontSize: 11, color: C.grey30, marginTop: 18 }}>Sample figures for layout only.</div>
      </div>
      <PageFooter color={C.paleBlue} title="KPMG AI theme" page={6} />
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
