// Shared building blocks for the KPMG theme previews (08-themes).
// Colours come from extract/01-colors/palette.json (observed in the 2026 PDFs).
import React from "react";

export const C = {
  blue: "#00338D", // KPMG Blue: text, headlines, dominant brand colour
  cobalt: "#1E49E2", // 2026 refresh: full-bleed covers, gradients
  darkBlue: "#0C233C", // deep navy panels
  ink: "#050B2E", // near-black navy used under glowing AI imagery
  pacific: "#00B8F5", // accent numbers, rules, highlighted words
  lightBlue: "#76D2FF",
  paleBlue: "#ACEAFF",
  purple: "#7213EA",
  lightPurple: "#B497FF",
  darkPurple: "#510DBC",
  magenta: "#AB0D82",
  tint20: "#D2DBF9",
  tint10: "#E9EDFC",
  tint5: "#F3F6FF",
  grey60: "#666666",
  grey30: "#B2B2B2",
  grey10: "#E5E5E5",
  white: "#FFFFFF",
} as const;

// KPMG Bold and Univers are licensed. The stacks fall back to Arial Narrow / Arial,
// and to Barlow Condensed when the gallery page can load Google Fonts.
export const FONT = {
  display: '"KPMG Bold", "KPMG", "Arial Narrow", "Barlow Condensed", "Roboto Condensed", Arial, sans-serif',
  body: '"Univers LT Std", "Univers", Arial, Helvetica, sans-serif',
};

// Photos and logos are referenced from the existing library, relative to the page
// that renders the preview (08-themes/index.html sits next to 04-photos etc.).
export let ASSET_BASE = "../";
export const setAssetBase = (b: string) => (ASSET_BASE = b);
export const asset = (p: string) => ASSET_BASE + p;

const LOGO_PATH =
  "M179.241 16.912H169.861L171.4 22.976H152.58499L151.04199 16.912H141.965V18.155C142.099 18.842 142.22299 19.558 142.403 20.326 144.04599 26.857 148.449 33.323 156.04399 33.323 159.056 33.323 162.039 32.203 161.62599 28.139H172.82199C173.264 30.036 174.00601 33.272 171.883 36.239 169.50099 39.469 164.703 40.761 158.48 40.761 154.032 40.761 147.565 40.06001 141.965 36.495V69.472H179.241V16.912M157.239 8.03101C155.109 7.655 152.991 7.397 150.969 7.397 145.599 7.397 141.863 9.84801 141.784 15.52H159.144L157.239 8.03101M135.76 38.053 135.747 30.51801C133.146 27.013 131.539 23.17801 130.778 20.09801 130.492 19.02901 130.299 17.97101 130.189 16.912H124.713L129.383 38.618 113.63599 38.62801 99.521 16.912H98.498V69.472H135.76V38.053M114.95499 16.912H109.34799L117.836 29.951 114.95499 16.912M92.341 38.661H83.00999L76.61301 16.912H66.72501C71.76199 18.72501 74.82999 22.20399 75.78 27.37801 76.558 31.373 76.194 34.01 74.517 35.98 72.00299 38.922 66.96899 38.68401 62.505 38.68401 61.71399 38.68401 55.105 38.661 55.105 38.661V69.472H92.341V38.661M86.377 16.912 90.29999 30.51801 90.439 16.912H86.377M59.25999 22.086H59.24899C58.88599 22.064 58.513 22.035 58.104 22.035 57.56299 22.03 57.131 22.015 56.73399 22.015L54.35001 22.035 55.44501 26.019 55.97501 28 57.23199 32.626C57.782 32.626 58.315 32.649 58.83899 32.649H60.687C63.83701 32.649 65.83301 32.472 66.55899 31.48 67.12 30.736 67.03799 29.455 66.388 27.499 65.26099 24.145 63.83701 22.41901 59.25999 22.086M48.901 36.735 48.31999 34.846 42.983 17.51801 42.771 16.912H25.23399L23.866 19.74001 42.771 38.618H30.627L15.839 23.04201 20.627 38.618H11.666V69.472H48.901V36.735M140.54199 70.866V35.494C139.293 34.52901 138.206 33.482 137.198 32.357V70.866H97.099V38.661H93.77299V70.866H53.664V38.618H50.338V70.866H10.233V34.101L0 .77299H8.99899L13.52699 15.52H14.825L22.286 .77299H33.159L25.912 15.52H42.355L37.79199 .77299H47.625L52.13 15.485H54.298V15.52H57.388 57.63199 76.194L71.851 .81801H81.76099L85.97101 15.52H90.439L90.554 .81801H98.87601L108.41901 15.52H114.66299L111.44901 .81801H121.20799L124.38899 15.52H130.022C129.798 10.976 130.98999 6.83301 134.09 4.039 137.884 .63701 143.687 0 147.985 0 153.875 0 159.97699 .81801 166.117 2.15201L169.51 15.52H180.651V70.866H140.54199";

/** KPMG logo rebuilt from the tech report vector (03-logos). Keep clear space of one "K" height. */
export function KpmgLogo({ color = C.white, width = 92 }: { color?: string; width?: number }) {
  return (
    <svg width={width} height={(width * 70.866) / 180.651} viewBox="0 0 180.651 70.866" aria-label="KPMG">
      <path transform="matrix(1,0,0,-1,0,70.866)" d={LOGO_PATH} fill={color} />
    </svg>
  );
}

/** A 16:9 slide designed at 1280 × 720 and scaled to `width`. */
export function Slide({
  width = 1280,
  background,
  children,
  style,
}: {
  width?: number;
  background: string;
  children: React.ReactNode;
  style?: React.CSSProperties;
}) {
  const s = width / 1280;
  return (
    <div style={{ width, height: 720 * s, overflow: "hidden", position: "relative", borderRadius: 4, flex: "none" }}>
      <div
        style={{
          width: 1280,
          height: 720,
          transform: `scale(${s})`,
          transformOrigin: "0 0",
          position: "absolute",
          inset: 0,
          background,
          fontFamily: FONT.body,
          color: C.blue,
          ...style,
        }}
      >
        {children}
      </div>
    </div>
  );
}

export const display = (size: number, color: string, extra: React.CSSProperties = {}): React.CSSProperties => ({
  fontFamily: FONT.display,
  fontWeight: 700,
  fontSize: size,
  lineHeight: 0.98,
  letterSpacing: "-0.01em",
  color,
  margin: 0,
  ...extra,
});

/** Cover strap line and legal footer, the two lines every 2026 KPMG page carries. */
export function CoverFooter({ color = C.white, right }: { color?: string; right?: string }) {
  return (
    <div style={{ position: "absolute", left: 64, right: 64, bottom: 36, display: "flex", justifyContent: "space-between", fontSize: 15, fontWeight: 700, color }}>
      <span>KPMG. Make the Difference.</span>
      {right && <span>{right}</span>}
    </div>
  );
}

export function PageFooter({ color = C.blue, title, page }: { color?: string; title: string; page: number }) {
  return (
    <div style={{ position: "absolute", left: 64, right: 64, bottom: 26, display: "flex", justifyContent: "space-between", fontSize: 10, color, opacity: 0.85 }}>
      <span>© 2026 Copyright owned by one or more of the KPMG International entities. KPMG International entities provide no services to clients. All rights reserved.</span>
      <span>
        {title} | {page}
      </span>
    </div>
  );
}

/** Theme metadata shared by every recipe's demo file and read by the gallery. */
export type ThemeMeta = {
  id: string;
  name: string;
  mode: "light" | "dark";
  tagline: string;
  sources: string;
  palette: { name: string; hex: string; role: string }[];
};
