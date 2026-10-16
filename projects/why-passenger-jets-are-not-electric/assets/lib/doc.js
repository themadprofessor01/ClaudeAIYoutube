/*
 * doc.js — documentary motion-graphics library for "Why Passenger Jets Are Not Electric".
 * Photoreal CG plates (rendered in Blender, assets/plates/*.jpg) are composited with HUD-style
 * graphics. Every animation goes on the scene's single paused GSAP timeline (seekable, deterministic).
 * Colour code: AMBER = jet fuel / combustion, CYAN = battery / electricity, RED = limit exceeded.
 */
(function () {
  const C = { amber: "#F2A33A", cyan: "#39C6F4", red: "#FF4B3E", text: "#F2F4F5", muted: "#8A949C", panel: "rgba(8,12,16,.62)" };

  const CSS = `
  @font-face { font-family: "Inter"; font-weight: 400; src: url("assets/fonts/inter-latin-400-normal.woff2") format("woff2"); }
  @font-face { font-family: "Inter"; font-weight: 500; src: url("assets/fonts/inter-latin-500-normal.woff2") format("woff2"); }
  @font-face { font-family: "Inter"; font-weight: 600; src: url("assets/fonts/inter-latin-600-normal.woff2") format("woff2"); }
  @font-face { font-family: "Inter"; font-weight: 700; src: url("assets/fonts/inter-latin-700-normal.woff2") format("woff2"); }
  @font-face { font-family: "Inter"; font-weight: 800; src: url("assets/fonts/inter-latin-800-normal.woff2") format("woff2"); }
  @font-face { font-family: "Mono"; font-weight: 400; src: url("assets/fonts/jetbrains-mono-latin-400-normal.woff2") format("woff2"); }
  @font-face { font-family: "Mono"; font-weight: 500; src: url("assets/fonts/jetbrains-mono-latin-500-normal.woff2") format("woff2"); }
  .cam { position:absolute; inset:0; overflow:hidden; background:#000; }
  .cam .shot { position:absolute; inset:0; visibility:hidden; overflow:hidden; }
  .pw { position:absolute; inset:0; overflow:hidden; }
  .pw > img, .pw > video { position:absolute; left:0; top:0; width:100%; height:100%; object-fit:cover; display:block; }
  .lbl { position:absolute; font-family:"Inter"; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:${C.text};
         font-size:26px; white-space:nowrap; text-shadow:0 2px 12px rgba(0,0,0,.65); }
  .lbl .sub { display:block; font-family:"Mono"; font-weight:400; letter-spacing:.02em; font-size:20px; color:${C.muted}; text-transform:none; margin-top:6px; }
  .big { position:absolute; left:0; right:0; text-align:center; font-family:"Inter"; font-weight:800; color:${C.text};
         letter-spacing:-.02em; text-shadow:0 4px 40px rgba(0,0,0,.55); line-height:1; }
  .mono { font-family:"Mono"; font-weight:500; font-variant-numeric:tabular-nums; }
  .chap { position:absolute; left:84px; bottom:86px; font-family:"Inter"; font-weight:600; font-size:22px; letter-spacing:.22em;
          color:${C.text}; text-transform:uppercase; padding-top:14px; border-top:1px solid rgba(242,244,245,.6); text-shadow:0 2px 10px rgba(0,0,0,.6); }
  .chap b { font-family:"Mono"; font-weight:500; color:${C.muted}; margin-right:18px; letter-spacing:.05em; }
  .card { position:absolute; padding:18px 24px; background:${C.panel}; border-left:3px solid ${C.cyan}; backdrop-filter:blur(6px);
          font-family:"Inter"; color:${C.text}; }
  .card .t { font-weight:700; font-size:28px; letter-spacing:.06em; text-transform:uppercase; }
  .card .r { font-family:"Mono"; font-size:21px; color:#C9D2D8; margin-top:8px; }
  .vig { position:absolute; inset:0; pointer-events:none; background:radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,.55) 100%); }
  .gauge { position:absolute; width:150px; font-family:"Mono"; color:${C.text}; }
  .gauge .track { position:absolute; left:46px; width:30px; background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.35); }
  .gauge .fill { position:absolute; left:0; right:0; bottom:0; height:0; background:linear-gradient(0deg, ${C.cyan}, #9BE3FF); box-shadow:0 0 18px ${C.cyan}; }
  .gauge .redl { position:absolute; left:28px; width:66px; height:2px; background:${C.red}; box-shadow:0 0 10px ${C.red}; }
  .gauge .redt { position:absolute; left:100px; font-size:16px; color:${C.red}; white-space:nowrap; letter-spacing:.06em; }
  .gauge .val { position:absolute; left:0; font-size:44px; font-weight:500; white-space:nowrap; }
  .gauge .cap { position:absolute; left:0; font-family:"Inter"; font-weight:600; font-size:17px; letter-spacing:.16em; color:${C.muted}; white-space:nowrap; }
  .bracket { position:absolute; border:2px solid rgba(255,255,255,.85); }
  .flash { position:absolute; inset:0; background:#fff; opacity:0; pointer-events:none; }
  .black { position:absolute; inset:0; background:#000; opacity:0; pointer-events:none; }
  .glow { position:absolute; border-radius:50%; pointer-events:none; mix-blend-mode:screen; }
  .lb { position:absolute; left:0; right:0; height:132px; background:#000; z-index:20; }
  `;
  if (!document.getElementById("doc-css")) {
    const st = document.createElement("style");
    st.id = "doc-css";
    st.textContent = CSS;
    document.head.appendChild(st);
  }

  // ---------------------------------------------------------------- builders (HTML strings)
  // A plate is a CG still (assets/plates/<key>.jpg) or, when a GPU-rendered animated clip exists
  // (listed in window.CLIPS by tools/build.mjs), a video (assets/clips/<key>.mp4). Video timing
  // (data-start / data-duration) is filled in by shots() once the shot's on-screen window is known.
  const plate = (id, key, style = "") => (window.CLIPS && window.CLIPS[key])
    ? `<div class="pw" id="${id}" style="${style}"><video class="clip plate-v" id="${id}-v" data-key="${key}" src="assets/clips/${key}.mp4" muted playsinline data-track-index="5"></video></div>`
    : `<div class="pw" id="${id}" style="${style}"><img src="assets/plates/${key}.jpg" data-key="${key}"></div>`;
  const vig = (a = 0.55) => `<div class="vig" style="background:radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,${a}) 100%)"></div>`;
  /** label with optional leader line to a point. anchor: 'l' text starts at x; 'r' text ends at x */
  function lbl(id, x, y, text, o = {}) {
    const col = o.color || C.text, size = o.size || 26, sub = o.sub ? `<span class="sub">${o.sub}</span>` : "";
    const pos = o.anchor === "r" ? `right:${1920 - x}px;text-align:right;` : o.anchor === "c" ? `left:${x}px;transform:translateX(-50%);text-align:center;` : `left:${x}px;`;
    let lead = "";
    if (o.to) {
      const [x2, y2] = o.to;
      const sx = o.anchor === "r" ? x + 10 : x - 10, sy = y + size * 0.6;
      lead = `<svg style="position:absolute;left:0;top:0;width:1920px;height:1080px;overflow:visible;pointer-events:none" id="${id}-ld">
        <path d="M${sx},${sy} L${x2},${y2}" stroke="${col}" stroke-width="1.6" fill="none" opacity=".9"/>
        <circle cx="${x2}" cy="${y2}" r="5" fill="${col}"/><circle cx="${x2}" cy="${y2}" r="12" fill="none" stroke="${col}" stroke-width="1.2" opacity=".6"/></svg>`;
    }
    return `<div id="${id}" style="position:absolute;inset:0;pointer-events:none">${lead}<div class="lbl" id="${id}-t" style="${pos}top:${y}px;font-size:${size}px;color:${col}">${text}${sub}</div></div>`;
  }
  const big = (id, text, o = {}) =>
    `<div class="big ${o.mono ? "mono" : ""}" id="${id}" style="top:${o.y ?? 420}px;font-size:${o.size || 190}px;color:${o.color || C.text};${o.style || ""}">${text}</div>`;
  const chap = (id, n, title) => `<div class="chap" id="${id}"><b>${n}</b>${title}</div>`;
  function card(id, x, y, title, rows, col = C.cyan) {
    return `<div class="card" id="${id}" style="left:${x}px;top:${y}px;border-left-color:${col}"><div class="t">${title}</div>${rows.map((r, i) => `<div class="r" id="${id}-r${i}">${r}</div>`).join("")}</div>`;
  }
  /** vertical load gauge. h = track height, max = value at the top, red = red-line value */
  function gauge(id, x, y, o = {}) {
    const h = o.h || 520, max = o.max || 180, red = o.red;
    const ry = red != null ? h - (red / max) * h : null;
    return `<div class="gauge" id="${id}" style="left:${x}px;top:${y}px;height:${h + 140}px">
      <div class="cap" style="top:0">${o.cap || "AIRCRAFT WEIGHT"}</div>
      <div class="val" id="${id}-val" style="top:30px">${o.v0 || "0 t"}</div>
      <div class="track" style="top:110px;height:${h}px"><div class="fill" id="${id}-fill"></div></div>
      ${ry != null ? `<div class="redl" style="top:${110 + ry}px"></div><div class="redt" style="top:${110 + ry - 22}px">${o.redLabel || "MAX TAKEOFF"}</div>` : ""}
    </div>`;
  }
  const glow = (id, x, y, r, col, a = 0.8) =>
    `<div class="glow" id="${id}" style="left:${x - r}px;top:${y - r}px;width:${2 * r}px;height:${2 * r}px;background:radial-gradient(circle, ${hexA(col, a)} 0%, ${hexA(col, a * 0.35)} 35%, rgba(0,0,0,0) 70%)"></div>`;
  function hexA(hex, a) {
    const n = parseInt(hex.slice(1), 16);
    return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`;
  }
  const brackets = (id, x, y, w, h, col = "rgba(255,255,255,.85)") => {
    const s = 34, b = (st) => `<div class="bracket" style="${st};border-color:${col}"></div>`;
    return `<div id="${id}" style="position:absolute;inset:0;pointer-events:none">${b(`left:${x}px;top:${y}px;width:${s}px;height:${s}px;border-right:none;border-bottom:none`)}${b(`left:${x + w - s}px;top:${y}px;width:${s}px;height:${s}px;border-left:none;border-bottom:none`)}${b(`left:${x}px;top:${y + h - s}px;width:${s}px;height:${s}px;border-right:none;border-top:none`)}${b(`left:${x + w - s}px;top:${y + h - s}px;width:${s}px;height:${s}px;border-left:none;border-top:none`)}</div>`;
  };
  const svg = (id, inner, extra = "") => `<svg id="${id}" viewBox="0 0 1920 1080" style="position:absolute;inset:0;width:1920px;height:1080px;overflow:visible;pointer-events:none" ${extra}>${inner}</svg>`;

  // ---------------------------------------------------------------- motion helpers
  const E = { out: "expo.out", inout: "sine.inOut", pow: "power2.out" };
  function fadeIn(tl, el, t, d = 0.35) { tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: d, ease: "power1.out" }, t); }
  function fadeOut(tl, el, t, d = 0.3) { tl.to(el, { opacity: 0, duration: d, ease: "power1.in" }, t); }
  /** label appearance: slide 24px + fade, expo-out; leader line draws */
  function show(tl, id, t, o = {}) {
    const dx = o.dx ?? -24;
    tl.fromTo(`#${id}-t`, { opacity: 0, x: dx }, { opacity: 1, x: 0, duration: 0.5, ease: E.out }, t);
    const ld = document.querySelector(`#${id}-ld path`);
    if (ld) {
      tl.fromTo(`#${id}-ld path`, { strokeDasharray: 2000, strokeDashoffset: 2000 }, { strokeDashoffset: 0, duration: 0.45, ease: "power2.out" }, t - 0.15);
      tl.fromTo(`#${id}-ld circle`, { opacity: 0, scale: 0, transformOrigin: "50% 50%" }, { opacity: 1, scale: 1, duration: 0.3, ease: E.out }, t - 0.2);
    }
    if (o.until != null) tl.to(`#${id}`, { opacity: 0, duration: 0.25 }, o.until);
  }
  function hide(tl, id, t) { tl.to(`#${id}`, { opacity: 0, duration: 0.25 }, t); }
  /** big number slam: scale from 1.25 + blur to 1 */
  function slam(tl, el, t, d = 0.5) {
    tl.fromTo(el, { opacity: 0, scale: 1.25, filter: "blur(14px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: d, ease: E.out }, t);
  }
  function chapter(tl, id, t, d = 3.2) {
    tl.fromTo(`#${id}`, { opacity: 0, x: -30 }, { opacity: 1, x: 0, duration: 0.6, ease: E.out }, t);
    tl.to(`#${id}`, { opacity: 0, duration: 0.5 }, t + d);
  }
  /** count a number up into el's textContent (tabular figures recommended) */
  function count(tl, sel, t, from, to, d, fmt = (v) => Math.round(v).toLocaleString("en-US")) {
    const o = { v: from };
    const el = document.querySelector(sel);
    tl.fromTo(o, { v: from }, { v: to, duration: d, ease: "power2.out", onUpdate: () => { el.innerHTML = fmt(o.v); } }, t);
  }
  /** Ken Burns on a plate wrapper: scale + drift */
  function push(tl, el, t, d, s0 = 1.0, s1 = 1.08, x0 = 0, x1 = 0, y0 = 0, y1 = 0, ease = "sine.inOut") {
    tl.fromTo(el, { scale: s0, x: x0, y: y0, transformOrigin: "50% 50%" }, { scale: s1, x: x1, y: y1, duration: d, ease }, t);
  }
  function shake(tl, el, t, d = 0.35, amp = 8) {
    const n = Math.floor(d / 0.04);
    for (let i = 0; i < n; i++) tl.to(el, { x: (i % 2 ? 1 : -1) * amp * (1 - i / n), y: ((i % 3) - 1) * amp * 0.6 * (1 - i / n), duration: 0.04, ease: "none" }, t + i * 0.04);
    tl.to(el, { x: 0, y: 0, duration: 0.04 }, t + n * 0.04);
  }
  function draw(tl, sel, t, d = 0.6, ease = "power1.inOut") {
    tl.fromTo(sel, { strokeDasharray: 4000, strokeDashoffset: 4000 }, { strokeDashoffset: 0, duration: d, ease }, t);
  }

  /** shot list [[selector, t, transition]] — transitions: cut | fade | flash | dip | blur */
  function shots(tl, list, end) {
    window.__SHOTLOG = window.__SHOTLOG || [];
    list.forEach(([sel, t0, tr = "cut"], i) => {
      window.__SHOTLOG.push({ sel, t: +t0.toFixed(3), tr });
      const next = list[i + 1];
      const t1 = next ? next[1] : end;
      const fadeNext = next && (next[2] === "fade" || next[2] === "blur");
      if (t0 <= 0) gsap.set(sel, { visibility: "inherit" });
      else tl.set(sel, { visibility: "inherit" }, t0 - (tr === "fade" || tr === "blur" ? 0.0 : 0));
      if (next) tl.set(sel, { visibility: "hidden" }, t1 + (fadeNext ? 0.6 : 0));
      if (tr === "fade") tl.fromTo(sel, { opacity: 0 }, { opacity: 1, duration: 0.6, ease: "power1.inOut" }, t0);
      if (tr === "blur") tl.fromTo(sel, { opacity: 0, filter: "blur(20px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.6, ease: "power2.out" }, t0);
      if (tr === "dip") tl.fromTo(sel, { opacity: 0 }, { opacity: 1, duration: 0.5, ease: "power1.out" }, t0);
      if (tr === "fade" || tr === "blur") tl.set(sel, { zIndex: 2 }, t0).set(sel, { zIndex: 1 }, t0 + 0.6);
      // clip timing + plate usage (collected at build time → timeline/plates.json, the GPU render list)
      const el = document.querySelector(sel);
      const dur = t1 + (fadeNext ? 0.6 : 0) - t0;
      if (el) el.querySelectorAll("[data-key]").forEach((m) => {
        (window.__PLATEUSE = window.__PLATEUSE || []).push({ key: m.dataset.key, dur: +dur.toFixed(3) });
        if (m.tagName === "VIDEO") { m.setAttribute("data-start", Math.max(0, t0).toFixed(3)); m.setAttribute("data-duration", (dur + 0.05).toFixed(3)); }
      });
    });
  }
  /** white flash over everything at t */
  function flash(tl, sel, t, peak = 0.85, d = 0.5) {
    tl.fromTo(sel, { opacity: 0 }, { opacity: peak, duration: 0.08, ease: "none" }, t).to(sel, { opacity: 0, duration: d, ease: "power2.out" }, t + 0.08);
  }

  // ---------------------------------------------------------------- scene / cues / sfx (shared engine)
  window.__SFX = window.__SFX || [];
  function sfx(scene, name, t, gain = 1) { window.__SFX.push({ scene, name, t: +t.toFixed(3), gain }); }
  function scene(id) {
    const list = [];
    return {
      id,
      add(name, html) { list.push(`<div class="shot" id="${id}-${name}">${html}</div>`); },
      mount(over = "") {
        const root = document.getElementById(id) || document.querySelector(`[data-hf-authored-id="${id}"]`);
        root.innerHTML = `<div class="cam" id="${id}-cam">${list.join("")}${over}</div>`;
      },
    };
  }
  function cue(CUES) {
    const wlen = (s) => s.replace(/[.?!]\s*/g, "@@@@@@@@").replace(/[,;:]\s*/g, "@@@@").length;
    return function q(id, phrase, off = 0) {
      const c = CUES[id];
      if (!c) throw new Error("no cue " + id);
      if (!phrase) return c[0] + off;
      if (phrase === "end") return c[1] + off;
      const i = c[2].indexOf(phrase);
      if (i < 0) throw new Error(`phrase "${phrase}" not in ${id}`);
      if (c[3] && c[3].length) {
        const norm = (w) => w.toLowerCase().replace(/[^a-z0-9$%']/g, "");
        const target = phrase.split(/\s+/).map(norm).filter(Boolean);
        const ws = c[3].map(([w]) => norm(w));
        const want = c[2].slice(0, i).split(/\s+/).filter(Boolean).length * (ws.length / Math.max(1, c[2].split(/\s+/).filter(Boolean).length));
        let best = -1, bestD = 1e9;
        for (let k = 0; k <= ws.length - target.length; k++) {
          let ok = true;
          for (let m = 0; m < target.length; m++) {
            const a = ws[k + m], b = target[m];
            if (!(a === b || (m === target.length - 1 && a.startsWith(b)) || (m === 0 && a.endsWith(b)))) { ok = false; break; }
          }
          if (ok && Math.abs(k - want) < bestD) { best = k; bestD = Math.abs(k - want); }
        }
        if (best >= 0) return c[3][best][1] + off;
        (window.__CUEMISS = window.__CUEMISS || []).push(id + ": " + phrase);
      }
      return c[0] + (c[1] - c[0]) * (wlen(c[2].slice(0, i)) / wlen(c[2])) + off;
    };
  }

  window.D = { C, plate, vig, lbl, big, chap, card, gauge, glow, brackets, svg, hexA,
    fadeIn, fadeOut, show, hide, slam, chapter, count, push, shake, draw, shots, flash, sfx, scene, cue };
})();
