#!/usr/bin/env node
// Check a docs folder before committing it: every ```mermaid block must parse
// with the real mermaid parser (in headless Chrome), and every relative link or
// image in every .md file must resolve.
//
//   node check-docs.mjs <docs-folder> [extra.md ...]
//
// Needs Playwright resolvable from the current directory (run it from a project
// that has `playwright` installed, or set NODE_PATH) and Google Chrome, or set
// CHANNEL= to use Playwright's bundled Chromium. MERMAID=<version> pins mermaid
// (default 11.4.1). Exit code 1 on any failure.
import { readFileSync, readdirSync, existsSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import { join, dirname, resolve } from "node:path";

const [root, ...extra] = process.argv.slice(2);
if (!root) {
  console.error("usage: node check-docs.mjs <docs-folder> [extra.md ...]");
  process.exit(2);
}
let chromium;
try {
  ({ chromium } = createRequire(join(process.cwd(), "noop.js"))("playwright"));
} catch {
  console.error("playwright not found from this directory: npm i -D playwright, or set NODE_PATH");
  process.exit(2);
}

const files = [];
(function walk(d) {
  for (const f of readdirSync(d)) {
    const p = join(d, f);
    if (statSync(p).isDirectory()) walk(p);
    else if (p.endsWith(".md")) files.push(p);
  }
})(resolve(root));
files.push(...extra.map((f) => resolve(f)));

const blocks = [];
let links = 0;
let badLinks = 0;
for (const f of files) {
  const text = readFileSync(f, "utf8");
  for (const m of text.matchAll(/```mermaid\n([\s\S]*?)```/g)) blocks.push({ f, src: m[1] });
  for (const m of text.matchAll(/\]\(([^)\s]+)\)/g)) {
    const href = m[1];
    if (/^(https?:|mailto:|#)/.test(href)) continue;
    links++;
    const target = resolve(dirname(f), decodeURI(href.split("#")[0]));
    if (!existsSync(target)) {
      badLinks++;
      console.log("BROKEN LINK", f, href);
    }
  }
}

let bad = 0;
if (blocks.length) {
  const channel = process.env.CHANNEL ?? "chrome";
  const browser = await chromium.launch(channel ? { channel } : {});
  const page = await browser.newPage();
  await page.setContent("<html><body></body></html>");
  const version = process.env.MERMAID ?? "11.4.1";
  await page.addScriptTag({ url: `https://cdn.jsdelivr.net/npm/mermaid@${version}/dist/mermaid.min.js` });
  await page.evaluate(() => window.mermaid.initialize({ startOnLoad: false }));
  for (const b of blocks) {
    const r = await page.evaluate(async (src) => {
      try {
        await window.mermaid.parse(src);
        return "ok";
      } catch (e) {
        return String(e.message || e).slice(0, 300);
      }
    }, b.src);
    if (r !== "ok") bad++;
    console.log(r === "ok" ? "ok  " : "FAIL", b.f, b.src.split("\n")[0], r === "ok" ? "" : r);
  }
  await browser.close();
}
console.log(`mermaid: ${blocks.length - bad}/${blocks.length} parse; links: ${links - badLinks}/${links} resolve`);
process.exit(bad || badLinks ? 1 : 0);
