// Rebuilds index.html from the .demo.tsx files.
// Usage (needs Node 18+): npm i react@18.3.1 react-dom@18.3.1 esbuild@0.23.1 && node build.mjs
import { build } from "esbuild";
import { writeFileSync } from "node:fs";

const out = await build({
  entryPoints: ["_shared/gallery.tsx"],
  bundle: true,
  minify: true,
  write: false,
  format: "iife",
  jsx: "automatic",
  define: { "process.env.NODE_ENV": '"production"' },
});
const js = out.outputFiles[0].text.replace(/<\/script/g, "<\\/script");

writeFileSync(
  "index.html",
  `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>KPMG theme recipes</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700&display=swap">
<style>html,body{margin:0;background:#F3F6FF}*{box-sizing:border-box}code{font-size:.9em;color:#1E49E2}</style>
</head>
<body><div id="root"></div><script>${js}</script></body>
</html>
`
);
console.log("index.html written");
