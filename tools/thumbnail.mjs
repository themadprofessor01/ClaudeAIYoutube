// Render docs/thumbnail_1.png (1280x720) using the same rig.js art as the video.
// usage: NODE_PATH=$(npm root -g) node tools/thumbnail.mjs
import fs from "node:fs";
import path from "node:path";
import http from "node:http";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");

const page = `<!doctype html><html><head><meta charset="utf-8">
<script src="/assets/lib/gsap.min.js"></script><script src="/assets/lib/rig.js"></script>
<style>
@font-face{font-family:"HandSC";src:url("/assets/fonts/PatrickHandSC.woff2") format("woff2")}
html,body{margin:0;width:1920px;height:1080px;overflow:hidden}
svg{position:absolute;inset:0;width:1920px;height:1080px}
.t{position:absolute;font-family:HandSC;color:#E4483B;-webkit-text-stroke:14px #272320;paint-order:stroke fill;letter-spacing:4px}
</style></head><body><svg id="s" viewBox="0 0 1920 1080"></svg>
<div class="t" style="left:0;right:0;top:20px;text-align:center;font-size:250px">WHY?!</div>
<script>
const { C, P, person, path, rect, line, circ, g, at, text } = R;
const handWith = (x, y, s, r, col) => g(null, rect(-260, -70, 160, 140, col, 18, 7) + P.hand(null, 0, 0, 1), at(x, y, s, r));
let burst = "M1440,600";
for (let i = 0; i < 24; i++) { const a = i / 24 * Math.PI * 2, rr = i % 2 ? 360 : 640; burst += " L" + (1440 + Math.cos(a) * rr) + "," + (600 + Math.sin(a) * rr); }
document.getElementById("s").innerHTML =
  rect(-10, -10, 970, 1100, "#C9D3DC", 0, 0) + rect(960, -10, 970, 1100, "#FFD84D", 0, 0) +
  path(burst + "Z", "#FFF1A8", 0) + line(960, 0, 960, 1080, 12) +
  person("a", { x: 480, y: 1180, s: 2.4, mouth: "flat" }) +
  handWith(260, 1000, 0.9, -40, C.yellow) +
  person("b", { x: 1430, y: 1180, s: 2.4, mouth: "laugh" }) +
  handWith(1790, 820, 0.9, 200, C.teal) +
  g(null, P.cross(null, 0, 0, 1.9, "#7A7F86"), at(160, 420)) +
  text(1110, 420, "HA", 120, C.red) + text(1780, 380, "HA!", 130, C.red);
// laughing face / bored face states
gsap.set("#a-eyes", { scaleY: 0.5, svgOrigin: "0 -222" });
gsap.set("#b-eyes", { opacity: 0 }); gsap.set("#b-happy", { opacity: 1 }); gsap.set("#b-blush", { opacity: 1 });
gsap.set("#b-armL", { rotation: 150, svgOrigin: "-26 -132" }); gsap.set("#b-armR", { rotation: -150, svgOrigin: "26 -132" });
gsap.set("#b-head", { rotation: -8, svgOrigin: "0 -150" });
</script></body></html>`;

const server = http.createServer((req, res) => {
  if (req.url === "/thumb") { res.setHeader("content-type", "text/html"); return res.end(page); }
  fs.readFile(path.join(ROOT, decodeURIComponent(req.url)), (e, d) => { if (e) { res.statusCode = 404; return res.end(); } res.end(d); });
});
await new Promise((r) => server.listen(0, r));
const exe = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome";
const browser = await chromium.launch({ executablePath: fs.existsSync(exe) ? exe : undefined });
const p = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2 / 3 });
await p.goto(`http://localhost:${server.address().port}/thumb`);
await p.evaluate(() => document.fonts.ready);
await p.waitForTimeout(300);
await p.screenshot({ path: path.join(ROOT, "docs/thumbnail_1.png") });
await browser.close();
server.close();
console.log("docs/thumbnail_1.png");
