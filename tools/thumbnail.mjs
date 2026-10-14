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
<div class="t" style="left:60px;top:40px;font-size:150px;transform:rotate(-3deg)">I CAME FOR</div>
<div class="t" style="left:120px;top:210px;font-size:230px;color:#FBF8F1">MILK...</div>
<script>
const { C, P, person, path, rect, line, circ, g, at, text } = R;
let burst = "M1400,620";
for (let i = 0; i < 24; i++) { const a = i / 24 * Math.PI * 2, rr = i % 2 ? 380 : 640; burst += " L" + (1400 + Math.cos(a) * rr) + "," + (620 + Math.sin(a) * rr); }
document.getElementById("s").innerHTML =
  rect(-10, -10, 1940, 1100, "#F6C744", 0, 0) + path(burst + "Z", "#FFE27A", 0) +
  person("a", { x: 640, y: 1250, s: 2.5, mouth: "O" }) +
  g(null, P.cart(null, 0, 0, 1.6) + P.chips(null, -170, -380, 1.3, C.orange) + P.chips(null, -10, -400, 1.3, C.red) + P.candle(null, 140, -380, 1.3) +
    P.product(null, -90, -280, 1.0, "box", C.purple, "SNAX") + P.product(null, 90, -290, 1.0, "can", C.green) + P.product(null, 230, -330, 1.0, "bottle", C.blue), at(1330, 1050)) +
  g(null, P.receipt(null, 0, 0, 1.2, 9, "$47.83"), at(1760, 600, 1, 8)) +
  g(null, P.product(null, 0, 0, 0.9, "milk") + P.cross(null, 0, -100, 1.6), at(320, 980));
gsap.set("#a-eyes", { scale: 1.15, svgOrigin: "0 -222" });
gsap.set("#a-armL", { rotation: 150, svgOrigin: "-26 -132" }); gsap.set("#a-armR", { rotation: -150, svgOrigin: "26 -132" });
gsap.set("#a-browL", { y: -10 }); gsap.set("#a-browR", { y: -10 }); gsap.set("#a-sweat", { opacity: 1 });
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
