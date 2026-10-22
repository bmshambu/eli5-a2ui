// Gallery for 08-themes: one recipe card per theme, click a card for the full live preview.
// Bundled into 08-themes/index.html by build.mjs.
import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import { C, FONT } from "./kpmg";
import * as corporate from "../kpmg-corporate/kpmg-corporate.demo";
import * as ai from "../kpmg-ai/kpmg-ai.demo";
import * as platform from "../kpmg-ai-platform/kpmg-ai-platform.demo";
import * as finance from "../kpmg-finance-data/kpmg-finance-data.demo";

const themes = [corporate, ai, platform, finance];
type T = (typeof themes)[number];

function Badge({ mode }: { mode: "light" | "dark" }) {
  const dark = mode === "dark";
  return (
    <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", padding: "3px 9px", borderRadius: 10, background: dark ? C.darkBlue : "transparent", color: dark ? C.white : C.grey60, border: dark ? "none" : `1px solid ${C.grey10}` }}>
      {mode.toUpperCase()}
    </span>
  );
}

function Card({ t, onOpen }: { t: T; onOpen: () => void }) {
  const W = 560;
  return (
    <button onClick={onOpen} style={{ all: "unset", cursor: "pointer", background: C.white, borderRadius: 10, boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 8px 24px rgba(0,51,141,0.08)", overflow: "hidden", display: "block" }}>
      <div style={{ position: "relative", width: W, maxWidth: "100%" }}>
        <t.Cover width={W} />
        <div style={{ position: "absolute", right: 14, bottom: 14, boxShadow: "0 6px 18px rgba(0,0,0,0.35)", border: `2px solid ${C.white}`, borderRadius: 4 }}>
          <t.Content width={200} />
        </div>
      </div>
      <div style={{ padding: "14px 18px 18px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontFamily: FONT.display, fontWeight: 700, fontSize: 26, color: C.blue }}>{t.theme.name}</span>
          <Badge mode={t.theme.mode} />
        </div>
        <div style={{ color: C.grey60, fontSize: 15, marginTop: 4 }}>{t.theme.tagline}</div>
        <div style={{ color: C.grey60, fontSize: 12, marginTop: 6 }}>{t.theme.sources}</div>
      </div>
    </button>
  );
}

function Detail({ t, onBack }: { t: T; onBack: () => void }) {
  return (
    <div style={{ maxWidth: 1000, margin: "0 auto" }}>
      <button onClick={onBack} style={{ all: "unset", cursor: "pointer", color: C.cobalt, fontWeight: 700, marginBottom: 16 }}>
        ← All themes
      </button>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <h1 style={{ fontFamily: FONT.display, fontSize: 44, color: C.blue, margin: 0 }}>{t.theme.name}</h1>
        <Badge mode={t.theme.mode} />
      </div>
      <p style={{ color: C.grey60, margin: "6px 0 16px" }}>
        {t.theme.tagline}. Recipe:{" "}
        <a href={`${t.theme.id}/${t.theme.id}.recipe.md`} style={{ color: C.cobalt }}>
          {t.theme.id}.recipe.md
        </a>{" "}
        · Live preview: <code>{t.theme.id}/{t.theme.id}.demo.tsx</code>
      </p>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 20 }}>
        {t.theme.palette.map((p) => (
          <div key={p.hex} style={{ display: "flex", alignItems: "center", gap: 8, background: C.white, padding: "6px 10px 6px 6px", borderRadius: 6, border: `1px solid ${C.grey10}` }}>
            <span style={{ width: 28, height: 28, borderRadius: 4, background: p.hex, border: `1px solid ${C.grey10}` }} />
            <span style={{ fontSize: 12, color: C.blue }}>
              <b>{p.name}</b> {p.hex}
              <br />
              <span style={{ color: C.grey60 }}>{p.role}</span>
            </span>
          </div>
        ))}
      </div>
      <div style={{ display: "grid", gap: 20 }}>
        <t.Cover width={1000} />
        <t.Content width={1000} />
      </div>
    </div>
  );
}

function App() {
  const initial = themes.find((t) => location.hash === `#${t.theme.id}`) ?? null;
  const [open, setOpen] = useState<T | null>(initial);
  const go = (t: T | null) => {
    setOpen(t);
    history.replaceState(null, "", t ? `#${t.theme.id}` : "#");
    window.scrollTo(0, 0);
  };
  return (
    <div style={{ minHeight: "100vh", background: C.tint5, padding: "32px 16px 48px", fontFamily: FONT.body, color: C.blue }}>
      {open ? (
        <Detail t={open} onBack={() => go(null)} />
      ) : (
        <div style={{ maxWidth: 1160, margin: "0 auto" }}>
          <h1 style={{ fontFamily: FONT.display, fontSize: 48, margin: 0 }}>KPMG theme recipes</h1>
          <p style={{ color: C.grey60, fontSize: 17, margin: "6px 0 24px" }}>
            Each recipe card is a <b style={{ color: C.blue }}>theme</b>. It comes with a live preview, so you can taste it before you cook.
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 560px), 1fr))", gap: 24, justifyItems: "center" }}>
            {themes.map((t) => (
              <Card key={t.theme.id} t={t} onOpen={() => go(t)} />
            ))}
          </div>
          <p style={{ textAlign: "center", color: C.grey60, fontSize: 14, marginTop: 28 }}>
            <code>recipe .md</code> + <code>live preview .demo.tsx</code> = one theme. A new flavour starts from{" "}
            <a href="_template/_template.recipe.md" style={{ color: C.cobalt }}>
              _template.recipe.md
            </a>
            .
          </p>
        </div>
      )}
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
