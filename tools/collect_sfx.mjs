// Collect the SFX cue log that each scene emits (R.sfx calls) while building its timeline.
// Loads every compositions/sXX.html into a bare harness page (gsap + rig.js), runs its
// script, reads window.__SFX, converts scene-local times to absolute using timing.json.
// usage: node tools/collect_sfx.mjs   → timeline/sfx_events.json
import fs from "node:fs";
import path from "node:path";
import http from "node:http";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require("playwright")); }
catch { ({ chromium } = require(path.join(process.env.NODE_PATH || "/opt/node22/lib/node_modules", "playwright"))); }

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const T = JSON.parse(fs.readFileSync(path.join(ROOT, "timeline/timing.json"), "utf8"));

const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split("?")[0]));
  if (req.url === "/__harness") {
    res.setHeader("content-type", "text/html");
    return res.end(`<!doctype html><html><head><script src="/assets/lib/gsap.min.js"></script><script src="/assets/lib/rig.js"></script></head><body><script>window.__timelines={};</script></body></html>`);
  }
  fs.readFile(p, (e, d) => { if (e) { res.statusCode = 404; return res.end(); } res.end(d); });
});
await new Promise((r) => server.listen(0, r));
const port = server.address().port;

const exe = process.env.CHROME || "/opt/pw-browsers/chromium-1194/chrome-linux/chrome";
const browser = await chromium.launch({ executablePath: fs.existsSync(exe) ? exe : undefined });
const events = [];
const shots = [];
for (const sec of T.sections) {
  const file = path.join(ROOT, "compositions", `${sec.id}.html`);
  if (!fs.existsSync(file)) continue;
  const page = await browser.newPage();
  const errs = [];
  page.on("pageerror", (e) => errs.push(e.message));
  await page.goto(`http://localhost:${port}/__harness`);
  await page.evaluate(async (src) => {
    const doc = new DOMParser().parseFromString(src, "text/html");
    const tpl = doc.querySelector("template");
    const frag = tpl.content.cloneNode(true);
    const scripts = [...frag.querySelectorAll("script")];
    scripts.forEach((s) => s.remove());
    document.body.appendChild(frag);
    for (const s of scripts) { const n = document.createElement("script"); n.textContent = s.textContent; document.body.appendChild(n); }
  }, fs.readFileSync(file, "utf8"));
  const log = await page.evaluate(() => window.__SFX || []);
  const shotlog = await page.evaluate(() => window.__SHOTLOG || []);
  for (const e of shotlog) shots.push({ scene: sec.id, shot: e.sel.split("-").pop(), transition: e.tr, abs: +(sec.start + e.t).toFixed(3) });
  if (errs.length) console.error(sec.id, "errors:", errs);
  for (const e of log) events.push({ ...e, abs: +(sec.start + e.t).toFixed(3) });
  console.log(sec.id, log.length, "sfx");
  await page.close();
}
await browser.close();
server.close();
events.sort((a, b) => a.abs - b.abs);
fs.writeFileSync(path.join(ROOT, "timeline/sfx_events.json"), JSON.stringify(events, null, 1));
fs.writeFileSync(path.join(ROOT, "timeline/shots.json"), JSON.stringify(shots, null, 1));
console.log("total", events.length, "sfx;", shots.length, "shots");
