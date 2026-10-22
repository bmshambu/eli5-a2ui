// Live preview for the KPMG AI Platform recipe (kpmg-ai-platform.recipe.md).
// Dark data-city cover, then light pages built around building-block architecture diagrams.
import React from "react";
import { C, FONT, KpmgLogo, Slide, display, asset, CoverFooter, PageFooter, ThemeMeta } from "../_shared/kpmg";

export const theme: ThemeMeta = {
  id: "kpmg-ai-platform",
  name: "KPMG AI Platform",
  mode: "light",
  tagline: "Building-block diagrams",
  sources: "from KPMG US AI Pulse (Jan 2026) + Global tech report 2026",
  palette: [
    { name: "KPMG Blue", hex: C.blue, role: "Block text, headings" },
    { name: "Cobalt", hex: C.cobalt, role: "Core platform layer" },
    { name: "Pacific Blue", hex: C.pacific, role: "Agents, connectors" },
    { name: "Blue Tint 20", hex: C.tint20, role: "Block fills" },
    { name: "Purple", hex: C.purple, role: "Governance rail" },
  ],
};

export function Cover({ width = 1280 }: { width?: number }) {
  return (
    <Slide width={width} background={`linear-gradient(90deg, ${C.ink} 0%, #071552 55%, #0A1E7A 100%)`}>
      <img
        src={asset("04-photos/04-technology-and-abstract/global-tech-report-2026_p26_08.jpg")}
        style={{ position: "absolute", right: 0, top: 0, width: 700, height: 720, objectFit: "cover", objectPosition: "60% 50%", opacity: 0.95, maskImage: "linear-gradient(90deg, transparent 0%, #000 45%)", WebkitMaskImage: "linear-gradient(90deg, transparent 0%, #000 45%)" }}
      />
      <div style={{ position: "absolute", left: 64, top: 56 }}>
        <KpmgLogo />
      </div>
      <div style={{ position: "absolute", left: 64, top: 200 }}>
        <div style={{ color: C.pacific, fontWeight: 700, fontSize: 15, marginBottom: 22 }}>Enterprise AI · 2026</div>
        <h1 style={display(84, C.white)}>From pilots</h1>
        <h1 style={display(84, C.white)}>to an enterprise</h1>
        <h1 style={display(84, C.pacific)}>AI platform</h1>
        <p style={{ color: C.white, fontSize: 18, lineHeight: 1.4, maxWidth: 470, marginTop: 24, opacity: 0.9 }}>
          A roadmap for launching AI that is predictable, governable and secure at scale
        </p>
      </div>
      <CoverFooter />
    </Slide>
  );
}

const Block = ({ label, tone = "tint", w = 1 }: { label: string; tone?: "tint" | "cobalt" | "pacific"; w?: number }) => {
  const s = {
    tint: { background: C.tint10, color: C.blue, border: `1.5px solid ${C.tint20}` },
    cobalt: { background: C.cobalt, color: C.white, border: `1.5px solid ${C.cobalt}` },
    pacific: { background: C.white, color: C.blue, border: `1.5px solid ${C.pacific}` },
  }[tone];
  return (
    <div style={{ ...s, flex: w, padding: "10px 12px", fontSize: 14, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", textAlign: "center", minHeight: 44 }}>
      {label}
    </div>
  );
};

/** The layered "building block" stack: one row per platform layer, side rails for cross-cutting controls. */
function PlatformStack() {
  const layers: { name: string; blocks: [string, "tint" | "cobalt" | "pacific"][] }[] = [
    { name: "Experiences", blocks: [["Copilots", "tint"], ["Workflow apps", "tint"], ["APIs", "tint"]] },
    { name: "Agents", blocks: [["Task agents", "pacific"], ["Orchestrator", "pacific"], ["Human in the loop", "pacific"]] },
    { name: "AI services", blocks: [["Model gateway", "cobalt"], ["Prompt & tool registry", "cobalt"], ["Evaluation", "cobalt"]] },
    { name: "Data foundation", blocks: [["Knowledge / RAG", "tint"], ["Data products", "tint"], ["Lineage", "tint"]] },
    { name: "Infrastructure", blocks: [["Cloud & GPU", "tint"], ["Identity", "tint"], ["Observability", "tint"]] },
  ];
  return (
    <div style={{ display: "flex", gap: 10 }}>
      <div style={{ flex: 1, display: "grid", gap: 8 }}>
        {layers.map((l) => (
          <div key={l.name} style={{ display: "flex", gap: 8, alignItems: "stretch" }}>
            <div style={{ width: 130, fontSize: 13, fontWeight: 700, color: C.cobalt, display: "flex", alignItems: "center" }}>{l.name}</div>
            {l.blocks.map(([b, t]) => (
              <Block key={b} label={b} tone={t} />
            ))}
          </div>
        ))}
      </div>
      {["Trust & governance", "Security & risk"].map((r, i) => (
        <div key={r} style={{ width: 46, background: i ? C.darkPurple : C.purple, color: C.white, fontSize: 13, fontWeight: 700, writingMode: "vertical-rl", transform: "rotate(180deg)", display: "flex", alignItems: "center", justifyContent: "center" }}>
          {r}
        </div>
      ))}
    </div>
  );
}

export function Content({ width = 1280 }: { width?: number }) {
  const steps = ["Pilot", "Platform foundation", "Scale use cases", "AI-native operations"];
  return (
    <Slide width={width} background={C.white}>
      <div style={{ position: "absolute", left: 64, top: 48, right: 64 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 14, fontWeight: 700, color: C.cobalt }}>
          <span style={{ width: 12, height: 12, background: C.cobalt, display: "inline-block" }} /> The platform blueprint
        </div>
        <h2 style={display(46, C.blue, { marginTop: 12 })}>Move from pilots to a governed AI platform</h2>
        <div style={{ display: "flex", margin: "24px 0 22px" }}>
          {steps.map((s, i) => (
            <div
              key={s}
              style={{
                flex: 1,
                background: [C.tint20, C.lightBlue, C.pacific, C.cobalt][i],
                color: i > 1 ? C.white : C.blue,
                padding: "12px 0 12px 34px",
                fontWeight: 700,
                fontSize: 15,
                clipPath: "polygon(0 0, calc(100% - 18px) 0, 100% 50%, calc(100% - 18px) 100%, 0 100%, 18px 50%)",
                marginLeft: i ? -8 : 0,
              }}
            >
              {String(i + 1).padStart(2, "0")} {s}
            </div>
          ))}
        </div>
        <PlatformStack />
      </div>
      <PageFooter title="KPMG AI Platform theme" page={9} />
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
