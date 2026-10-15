#!/usr/bin/env node
// Screenshot a static web app as it was at several commits.
//
//   node shots-at-commits.mjs --commits <sha>:<label>,<sha>:<label>,... --out <dir>
//        [--repo .] [--viewport 1280x720] [--serve-dir .] [--path /]
//        [--build "<shell command run inside each export>"] [--steps steps.mjs]
//
// Each commit is exported with `git archive` into a temp folder (never touches the
// working tree), optionally built, served by a throwaway no-store static server on a
// free port, and opened in a fresh browser context. Files are named
// <NN>-<label>-<screen>.png, NN = the commit's position in --commits.
//
// --steps points at a module whose default export drives the app and takes shots:
//   export default async function (page, shot, { sha, label }) {
//     await shot("01-setup");
//     await page.getByRole("button", { name: "Start" }).click();
//     await shot("02-board");
//   }
// Older commits often lack later screens: a failing step is logged and the run moves
// on to the next commit. Without --steps, only the landing page is captured.
// A manifest.json in --out records each commit's shots, step errors and console errors.
//
// Needs Playwright resolvable from the current directory and Google Chrome (or set
// CHANNEL= for bundled Chromium). Apps that need their own backend are out of scope:
// start the app's server per export instead of the static one.
import { execFileSync, execSync } from "node:child_process";
import { createServer } from "node:http";
import { mkdtempSync, mkdirSync, readFileSync, existsSync, statSync, writeFileSync, rmSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { join, resolve, extname, normalize } from "node:path";
import { pathToFileURL } from "node:url";

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, all) => (a.startsWith("--") ? [...acc, [a.slice(2), all[i + 1]]] : acc), [])
);
if (!args.commits || !args.out) {
  console.error("usage: node shots-at-commits.mjs --commits <sha>:<label>,... --out <dir> [options]");
  process.exit(2);
}
let chromium;
try {
  ({ chromium } = createRequire(join(process.cwd(), "noop.js"))("playwright"));
} catch {
  console.error("playwright not found from this directory: npm i -D playwright, or set NODE_PATH");
  process.exit(2);
}
const repo = resolve(args.repo ?? ".");
const out = resolve(args.out);
const [width, height] = (args.viewport ?? "1280x720").split("x").map(Number);
const steps = args.steps ? (await import(pathToFileURL(resolve(args.steps)).href)).default : null;
const commits = args.commits.split(",").map((c, i) => {
  const [sha, label = sha] = c.split(":");
  return { sha, label, nn: String(i + 1).padStart(2, "0") };
});
mkdirSync(out, { recursive: true });

const TYPES = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp", ".woff2": "font/woff2",
  ".wav": "audio/wav", ".mp3": "audio/mpeg", ".m4a": "audio/mp4", ".yaml": "text/plain", ".yml": "text/plain",
  ".txt": "text/plain", ".ico": "image/x-icon" };

function serve(dir) {
  const server = createServer((req, res) => {
    let p = normalize(decodeURIComponent(new URL(req.url, "http://x").pathname));
    let file = join(dir, p);
    if (!file.startsWith(dir)) return res.writeHead(403).end();
    if (existsSync(file) && statSync(file).isDirectory()) file = join(file, "index.html");
    if (!existsSync(file)) return res.writeHead(404).end();
    res.writeHead(200, { "Content-Type": TYPES[extname(file)] ?? "application/octet-stream", "Cache-Control": "no-store" });
    res.end(readFileSync(file));
  });
  return new Promise((ok) => server.listen(0, "127.0.0.1", () => ok(server)));
}

const browser = await chromium.launch(process.env.CHANNEL === "" ? {} : { channel: process.env.CHANNEL ?? "chrome" });
const manifest = [];
for (const c of commits) {
  const work = mkdtempSync(join(tmpdir(), `shot-${c.sha}-`));
  const entry = { ...c, date: "", subject: "", shots: [], stepError: null, consoleErrors: [] };
  try {
    [entry.date, entry.subject] = execFileSync("git", ["-C", repo, "log", "-1", "--format=%ci%n%s", c.sha]).toString().trim().split("\n");
    const tar = join(work, ".export.tar");
    execFileSync("git", ["-C", repo, "archive", "--format=tar", "-o", tar, c.sha]);
    execFileSync("tar", ["-x", "-f", tar, "-C", work]);
    rmSync(tar);
    // --build is the caller's own shell command, run inside the export.
    if (args.build) execSync(args.build, { cwd: work, stdio: "inherit" });
    const server = await serve(resolve(work, args["serve-dir"] ?? "."));
    const ctx = await browser.newContext({ viewport: { width, height } });
    const page = await ctx.newPage();
    page.on("console", (m) => m.type() === "error" && entry.consoleErrors.push(m.text()));
    page.on("pageerror", (e) => entry.consoleErrors.push(String(e)));
    const shot = async (name) => {
      const file = `${c.nn}-${c.label}-${name}.png`;
      await page.screenshot({ path: join(out, file) });
      entry.shots.push(file);
    };
    await page.goto(`http://127.0.0.1:${server.address().port}${args.path ?? "/"}`, { waitUntil: "load" });
    try {
      if (steps) await steps(page, shot, { sha: c.sha, label: c.label });
      else await shot("landing");
    } catch (e) {
      entry.stepError = String(e.message ?? e).split("\n")[0];
    }
    await ctx.close();
    server.close();
  } catch (e) {
    entry.stepError = `setup: ${String(e.message ?? e).split("\n")[0]}`;
  } finally {
    rmSync(work, { recursive: true, force: true });
  }
  manifest.push(entry);
  console.log(`${c.nn} ${c.sha} ${c.label}: ${entry.shots.length} shots${entry.stepError ? ` (stopped: ${entry.stepError})` : ""}`);
}
await browser.close();
writeFileSync(join(out, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
console.log(`manifest: ${join(out, "manifest.json")}`);
