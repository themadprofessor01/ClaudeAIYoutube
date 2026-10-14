/*
 * rig.js — shared drawing + motion library for "Why Can't You Tickle Yourself?"
 * Randos in 60s. Everything is drawn as SVG at runtime (no bitmaps), and every
 * animation goes onto the scene's single paused GSAP timeline, so frames are
 * fully seekable / deterministic.
 *
 * Coordinate space: every shot is an <svg viewBox="0 0 1920 1080">.
 * Characters are authored around their hips (0,0); feet at y=+170, head centre y=-215.
 */
(function () {
  const C = {
    ink: "#272320",
    paper: "#FBF8F1",
    paper2: "#F4EFE3",
    sky: "#A9D8EC",
    sky2: "#CFEAF4",
    sand: "#E8C47C",
    grass: "#9CC56B",
    wall: "#F4DFBF",
    wall2: "#EACB9C",
    floor: "#C58D5A",
    floor2: "#AE7746",
    orange: "#F08A3C",
    red: "#E4483B",
    teal: "#3FA7A0",
    blue: "#4C8BD6",
    yellow: "#F6C744",
    green: "#5DB35A",
    pink: "#F3A6B3",
    pinkDark: "#D9798A",
    purple: "#8E6BC8",
    gray: "#B9B4AA",
    gray2: "#E2DED5",
    night: "#1F2440",
    night2: "#2D3460",
    brown: "#7A5236",
    white: "#FFFFFF",
    mouth: "#5A2124",
    tongue: "#EF7C84",
  };
  const FONT = "'HandSC', 'Patrick Hand SC', cursive";
  const FONT2 = "'Hand', 'Patrick Hand', cursive";
  const SW = 7; // limb stroke width

  // ---------- tiny utils ----------
  const g = (id, inner, tr) =>
    `<g${id ? ` id="${id}"` : ""}${tr ? ` transform="${tr}"` : ""}>${inner}</g>`;
  const at = (x, y, s = 1, r = 0) =>
    `translate(${x} ${y})${s !== 1 ? ` scale(${s})` : ""}${r ? ` rotate(${r})` : ""}`;
  const line = (x1, y1, x2, y2, w = SW, c = C.ink) =>
    `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${c}" stroke-width="${w}" stroke-linecap="round"/>`;
  const path = (d, fill = "none", w = 6, c = C.ink, extra = "") =>
    `<path d="${d}" fill="${fill}" stroke="${c}" stroke-width="${w}" stroke-linecap="round" stroke-linejoin="round" ${extra}/>`;
  const circ = (cx, cy, r, fill = C.white, w = 6, c = C.ink, extra = "") =>
    `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${fill}" stroke="${c}" stroke-width="${w}" ${extra}/>`;
  const ell = (cx, cy, rx, ry, fill = C.white, w = 6, c = C.ink, extra = "") =>
    `<ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="${fill}" stroke="${c}" stroke-width="${w}" ${extra}/>`;
  const rect = (x, y, w, h, fill = C.white, rx = 10, sw = 6, c = C.ink, extra = "") =>
    `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${fill}" stroke="${c}" stroke-width="${sw}" ${extra}/>`;
  const text = (x, y, s, size = 64, fill = C.ink, anchor = "middle", extra = "", font = FONT) =>
    `<text x="${x}" y="${y}" font-family="${font}" font-size="${size}" fill="${fill}" text-anchor="${anchor}" dominant-baseline="middle" ${extra}>${s}</text>`;

  // seeded PRNG (mulberry32) — deterministic "randomness"
  function rng(seed) {
    let a = seed >>> 0;
    return function () {
      a |= 0;
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // ---------- filters / defs ----------
  // "Line boil": a few displacement filters with different seeds; we flip between them
  // at 8 fps to get the hand-drawn wobble of traditional animation.
  function defs(pfx) {
    let f = "";
    for (let i = 0; i < 3; i++) {
      f += `<filter id="${pfx}-boil${i}" x="-5%" y="-5%" width="110%" height="110%">
        <feTurbulence type="fractalNoise" baseFrequency="0.022" numOctaves="2" seed="${i * 7 + 3}" result="n"/>
        <feDisplacementMap in="SourceGraphic" in2="n" scale="4.5" xChannelSelector="R" yChannelSelector="G"/>
      </filter>`;
    }
    f += `<filter id="${pfx}-glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="18"/></filter>`;
    f += `<filter id="${pfx}-soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>`;
    return `<defs>${f}</defs>`;
  }

  // ---------- characters ----------
  const MOUTHS = {
    smile: path("M-20,-187 Q0,-168 20,-187", "none", 5),
    grin: path("M-24,-190 Q0,-186 24,-190 Q21,-160 0,-158 Q-21,-160 -24,-190 Z", C.mouth, 5) +
      path("M-11,-164 Q0,-174 11,-164 Q0,-158 -11,-164Z", C.tongue, 0),
    laugh: path("M-32,-196 Q0,-190 32,-196 Q29,-146 0,-143 Q-29,-146 -32,-196 Z", C.mouth, 5) +
      path("M-15,-152 Q0,-166 15,-152 Q0,-144 -15,-152Z", C.tongue, 0),
    flat: path("M-15,-180 L15,-180", "none", 5),
    o: ell(0, -177, 9, 12, C.mouth, 5),
    O: ell(0, -175, 15, 20, C.mouth, 5),
    frown: path("M-18,-172 Q0,-188 18,-172", "none", 5),
    wavy: path("M-22,-180 q5.5,-7 11,0 t11,0 t11,0 t11,0", "none", 4.5),
    smirk: path("M-17,-180 Q5,-175 19,-189", "none", 5),
    yell: path("M-22,-196 Q0,-200 22,-196 Q20,-150 0,-148 Q-20,-150 -22,-196 Z", C.mouth, 5),
  };

  const HAIR = {
    beanie: (col) =>
      path("M-58,-258 Q-60,-318 0,-320 Q60,-318 58,-258 Z", col, 6) +
      rect(-66, -272, 132, 28, col, 12, 6) +
      path("M-40,-270 L-40,-246 M-14,-270 L-14,-246 M12,-270 L12,-246 M38,-270 L38,-246", "none", 3, "rgba(0,0,0,.25)") +
      circ(0, -324, 14, col, 6),
    messy: (col) =>
      path(
        "M-62,-222 Q-70,-262 -48,-272 Q-50,-296 -20,-290 Q-10,-312 14,-296 Q38,-308 46,-282 Q72,-276 62,-236 Q52,-262 30,-262 Q14,-276 -6,-264 Q-26,-276 -40,-258 Q-56,-254 -62,-222Z",
        col, 6),
    bun: (col) =>
      circ(0, -292, 26, col, 6) +
      path("M-62,-214 Q-66,-276 0,-280 Q66,-276 62,-214 Q48,-256 0,-254 Q-48,-256 -62,-214Z", col, 6),
    curly: (col) => {
      let s = "";
      [[-50, -250], [-26, -272], [2, -280], [30, -272], [52, -250], [-60, -224], [62, -224]].forEach(
        ([x, y]) => (s += circ(x, y, 20, col, 5))
      );
      return s;
    },
    side: (col) =>
      path("M-64,-206 Q-70,-250 -46,-262 Q-30,-290 10,-286 Q56,-286 64,-226 Q40,-262 -6,-262 Q-40,-252 -50,-204 Z", col, 6),
    bald: () => "",
    sideburns: (col) =>
      path("M-62,-206 Q-66,-262 -30,-276 Q0,-290 34,-276 Q66,-262 62,-206 L56,-206 Q52,-246 20,-256 Q-10,-262 -40,-250 Q-56,-238 -56,-206 Z", col, 6) +
      rect(-62, -230, 12, 44, col, 4, 4) + rect(50, -230, 12, 44, col, 4, 4),
    ponytail: (col) =>
      path("M-62,-216 Q-66,-282 0,-284 Q66,-282 62,-216 Q44,-258 -8,-256 Q-44,-252 -62,-216Z", col, 6) +
      path("M56,-262 Q100,-262 96,-200 Q92,-170 76,-160 Q84,-206 58,-236 Z", col, 6),
  };

  /**
   * person(id, opts) → SVG string. Animatable sub-ids:
   *  id (whole body), id-torso, id-head, id-armL, id-foreL, id-armR, id-foreR,
   *  id-legL, id-shinL, id-legR, id-shinR, id-eyes, id-pupils, id-browL, id-browR,
   *  id-m-<mouth>, id-blush, id-sweat
   */
  function person(id, o = {}) {
    const {
      x = 960, y = 700, s = 1, shirt = C.yellow, hair = "beanie", hairColor = C.orange,
      coat = false, glasses = false, mouth = "smile", pants = null, flip = 1, skin = C.white,
      dress = null, tunic = null,
    } = o;
    const arm = (side) => {
      const sx = side === "L" ? -26 : 26;
      const sleeve = coat ? C.white : shirt;
      return g(`${id}-arm${side}`,
        path(`M${sx},-132 L${sx},-66`, "none", SW) +
        rect(sx - 15, -142, 30, 46, sleeve, 12, 5) +
        g(`${id}-fore${side}`, line(sx, -66, sx, 2) + circ(sx, 6, 8, skin, 5)));
    };
    const leg = (side) => {
      const hx = side === "L" ? -12 : 12;
      const fx = side === "L" ? -26 : 26;
      return g(`${id}-leg${side}`,
        line(hx, 4, hx, 88) +
        g(`${id}-shin${side}`, line(hx, 88, hx, 168) + line(hx, 168, fx, 170, SW)) +
        (pants ? path(`M${hx - 15},0 L${hx + 15},0 L${hx + 13},70 L${hx - 13},70Z`, pants, 5) : ""));
    };
    let torso = line(0, -150, 0, 4);
    if (tunic) torso += path("M-30,-146 Q0,-156 30,-146 L40,30 L22,22 L10,34 L-4,24 L-18,34 L-30,22 L-42,30 Z", tunic, 5);
    else if (dress) torso += path("M-26,-146 Q0,-154 26,-146 L56,40 Q0,52 -56,40 Z", dress, 6);
    else torso += path("M-34,-145 Q0,-156 34,-145 L38,10 Q0,17 -38,10 Z", shirt, 6);
    if (coat)
      torso += path("M-30,-146 L-44,62 L-6,62 L-4,-120 Z", C.white, 5) +
        path("M30,-146 L44,62 L6,62 L4,-120 Z", C.white, 5) +
        path("M-14,-146 L-2,-112 M14,-146 L2,-112", "none", 4);
    const eyes =
      g(`${id}-eyes`,
        circ(-22, -222, 14, C.white, 4) + circ(22, -222, 14, C.white, 4) +
        g(`${id}-pupils`, circ(-22, -221, 7, C.ink, 0) + circ(22, -221, 7, C.ink, 0) +
          circ(-19, -224, 2.2, C.white, 0) + circ(25, -224, 2.2, C.white, 0)));
    const happy = `<g id="${id}-happy" opacity="0">${path("M-34,-214 Q-22,-232 -10,-214 M10,-214 Q22,-232 34,-214", "none", 6)}</g>`;
    const brows =
      g(`${id}-browL`, path("M-36,-248 L-10,-250", "none", 5)) +
      g(`${id}-browR`, path("M10,-250 L36,-248", "none", 5));
    let mouths = "";
    for (const k in MOUTHS)
      mouths += `<g id="${id}-m-${k}" opacity="${k === mouth ? 1 : 0}">${MOUTHS[k]}</g>`;
    const gl = glasses
      ? circ(-22, -222, 21, "none", 4) + circ(22, -222, 21, "none", 4) + line(-1, -224, 1, -224, 4)
      : "";
    const head = g(`${id}-head`,
      circ(0, -215, 62, skin, 6) + (HAIR[hair] ? HAIR[hair](hairColor) : "") + eyes + happy + gl + brows + mouths +
      `<g id="${id}-blush" opacity="0">${ell(-40, -196, 11, 7, C.pink, 0)}${ell(40, -196, 11, 7, C.pink, 0)}</g>` +
      `<g id="${id}-sweat" opacity="0">${path("M70,-250 Q60,-232 70,-226 Q80,-232 70,-250Z", "#8FD0F0", 3)}</g>`);
    const body = leg("L") + leg("R") + arm("L") + g(`${id}-torso`, torso) + arm("R") + head;
    return g(null, `<g class="boil">` + g(id, g(`${id}-flip`, body, flip === -1 ? "scale(-1 1)" : "")) + `</g>`, at(x, y, s));
  }

  // joints: name → [svgOrigin, sign]. sign makes "positive" mean "outwards / up" for both sides.
  const JOINTS = {
    armL: ["-26 -132", 1], foreL: ["-26 -66", 1], armR: ["26 -132", -1], foreR: ["26 -66", -1],
    legL: ["-12 4", 1], shinL: ["-12 88", -1], legR: ["12 4", -1], shinR: ["12 88", 1],
    head: ["0 -150", 1], torso: ["0 4", 1],
  };

  /** pose(tl, id, {armL:deg, foreL:deg, ...}, t, dur=0.3, ease) */
  function pose(tl, id, p, t, dur = 0.3, ease = "power2.inOut") {
    for (const k in p) {
      if (!JOINTS[k]) continue;
      const [o, sgn] = JOINTS[k];
      const el = `#${id}-${k}`;
      if (dur <= 0) tl.set(el, { rotation: p[k] * sgn, svgOrigin: o }, t);
      else tl.to(el, { rotation: p[k] * sgn, svgOrigin: o, duration: dur, ease }, t);
    }
  }

  const BROWS = {
    neutral: [0, 0, 0],
    up: [0, 0, -9],
    angry: [16, -16, 4],
    worried: [-14, 14, -4],
    sly: [8, -2, 0],
  };
  /** expr(tl,id,{mouth, brows, look:[dx,dy], blush, sweat}, t) */
  function expr(tl, id, e, t) {
    if (e.mouth) for (const k in MOUTHS) tl.set(`#${id}-m-${k}`, { opacity: k === e.mouth ? 1 : 0 }, t);
    if (e.brows) {
      const [l, r, dy] = BROWS[e.brows];
      tl.to(`#${id}-browL`, { rotation: l, y: dy, svgOrigin: "-23 -249", duration: 0.15 }, t);
      tl.to(`#${id}-browR`, { rotation: r, y: dy, svgOrigin: "23 -249", duration: 0.15 }, t);
    }
    if (e.look) tl.to(`#${id}-pupils`, { x: e.look[0], y: e.look[1], duration: 0.18, ease: "power2.out" }, t);
    if (e.blush !== undefined) tl.to(`#${id}-blush`, { opacity: e.blush ? 1 : 0, duration: 0.2 }, t);
    if (e.sweat !== undefined) tl.to(`#${id}-sweat`, { opacity: e.sweat ? 1 : 0, duration: 0.2 }, t);
    if (e.eyes) {
      tl.set(`#${id}-eyes`, { opacity: e.eyes === "happy" ? 0 : 1 }, t);
      tl.set(`#${id}-happy`, { opacity: e.eyes === "happy" ? 1 : 0 }, t);
    }
    if (e.lids !== undefined) tl.to(`#${id}-eyes`, { scaleY: e.lids, svgOrigin: "0 -222", duration: 0.15 }, t);
  }
  function blink(tl, id, t) {
    tl.to(`#${id}-eyes`, { scaleY: 0.1, svgOrigin: "0 -222", duration: 0.06 }, t)
      .to(`#${id}-eyes`, { scaleY: 1, svgOrigin: "0 -222", duration: 0.08 }, t + 0.09);
  }
  /** idle: breathing bob + periodic blinks across [t0, t1] */
  function idle(tl, id, t0, t1, seed = 1) {
    const r = rng(seed);
    const dur = t1 - t0;
    const cyc = 1.6;
    const n = Math.max(0, Math.floor(dur / cyc) - 1);
    if (dur > 0.5)
      tl.fromTo(`#${id}-torso`, { scaleY: 1 }, { scaleY: 1.018, svgOrigin: "0 4", duration: cyc / 2, ease: "sine.inOut", yoyo: true, repeat: n * 2 + 1 }, t0);
    for (let t = t0 + 0.6 + r() * 1.5; t < t1 - 0.3; t += 2.2 + r() * 2.2) blink(tl, id, t);
  }
  /** laugh: shake body, flip mouths laugh/grin, head bob */
  function laugh(tl, id, t0, dur, amp = 1) {
    expr(tl, id, { mouth: "laugh", brows: "up", blush: 1, eyes: "happy" }, t0);
    const steps = Math.floor(dur / 0.14);
    for (let i = 0; i < steps; i++) {
      const tt = t0 + i * 0.14;
      tl.to(`#${id}-head`, { rotation: (i % 2 ? 6 : -6) * amp, svgOrigin: "0 -150", duration: 0.12, ease: "sine.inOut" }, tt);
      tl.to(`#${id}`, { y: i % 2 ? -10 * amp : 0, duration: 0.12, ease: "sine.inOut" }, tt);
      if (i % 4 === 2) tl.set(`#${id}-m-laugh`, { opacity: 0 }, tt).set(`#${id}-m-grin`, { opacity: 1 }, tt);
      if (i % 4 === 0) tl.set(`#${id}-m-laugh`, { opacity: 1 }, tt).set(`#${id}-m-grin`, { opacity: 0 }, tt);
    }
    tl.to(`#${id}-head`, { rotation: 0, svgOrigin: "0 -150", duration: 0.2 }, t0 + steps * 0.14);
    tl.to(`#${id}`, { y: 0, duration: 0.2 }, t0 + steps * 0.14);
  }
  /** flutter: oscillate one joint around a base pose angle (for scratching, poking, waving) */
  function flutter(tl, id, joint, base, t0, dur, amp = 12, period = 0.1) {
    const n = Math.floor(dur / period);
    for (let i = 0; i < n; i++) pose(tl, id, { [joint]: base + (i % 2 ? amp : -amp) }, t0 + i * period, period, "sine.inOut");
    pose(tl, id, { [joint]: base }, t0 + n * period, period);
  }
  /** talk: mouth flaps between given mouths for dur */
  function talk(tl, id, t0, dur, rest = "smile") {
    const seq = ["o", "smile", "O", "flat", "grin", "o"];
    let i = 0;
    for (let t = t0; t < t0 + dur - 0.1; t += 0.13, i++) expr(tl, id, { mouth: seq[i % seq.length] }, t);
    expr(tl, id, { mouth: rest }, t0 + dur);
  }
  /** walk in place cycle for dur */
  function walk(tl, id, t0, dur, step = 0.32, amp = 24) {
    const n = Math.floor(dur / step);
    for (let i = 0; i < n; i++) {
      const a = i % 2 ? amp : -amp;
      pose(tl, id, { legL: a, legR: -a, shinL: Math.abs(a) * 0.4, shinR: Math.abs(a) * 0.4, armL: -a * 0.7 + 8, armR: a * 0.7 + 8 }, t0 + i * step, step, "sine.inOut");
      tl.to(`#${id}`, { y: -8, duration: step / 2, ease: "sine.out", yoyo: true, repeat: 1 }, t0 + i * step);
    }
    pose(tl, id, { legL: 0, legR: 0, shinL: 0, shinR: 0, armL: 8, armR: 8 }, t0 + n * step, 0.2);
  }

  // ---------- props ----------
  const P = {};
  P.foot = (id, x, y, s = 1, r = 0) => g(null, g(id,
    // big bare foot, sole facing camera-left
    path("M-40,-260 Q-60,-120 -70,-20 Q-80,80 -10,96 Q70,110 92,40 Q110,-40 70,-120 Q50,-180 50,-260 Z", "#FFE9D6", 7) +
    path("M-30,40 Q10,70 60,30", "none", 4, "#D9A889") + path("M-40,-40 Q0,-20 40,-60", "none", 4, "#D9A889") +
    ell(-48, 20, 4, 7, "#D9A889", 0) +
    [[-56, 86, 15], [-24, 104, 17], [12, 108, 16], [46, 100, 15], [74, 82, 13]].map(([a, b, rr]) => circ(a, b + 10, rr, "#FFE9D6", 6)).join("")),
    at(x, y, s, r));
  P.hand = (id, x, y, s = 1, r = 0, skin = "#FFE9D6") => g(null, g(id,
    // pointing hand, finger pointing +x
    path("M-120,-36 L-40,-40 Q-20,-46 0,-34 L110,-34 Q132,-24 110,-12 L20,-10 Q30,4 22,16 Q34,26 22,38 Q30,52 14,58 L-40,60 L-120,56 Z", skin, 7) +
    path("M20,-10 L-6,-10 M22,16 L-4,16 M22,38 L-2,38", "none", 4) + path("M86,-34 Q92,-24 86,-12", "none", 3, "#C9977A")),
    at(x, y, s, r));
  P.feather = (id, x, y, s = 1, r = 0, col = C.teal) => g(null, g(id,
    path("M0,140 Q-4,0 0,-150", "none", 6) +
    path("M0,-150 Q70,-110 60,-20 Q50,40 4,90 Q-50,40 -60,-20 Q-70,-110 0,-150 Z", col, 6) +
    path("M2,-100 L40,-80 M2,-60 L46,-40 M2,-20 L44,0 M2,20 L34,40 M-2,-100 L-40,-80 M-2,-60 L-46,-40 M-2,-20 L-44,0 M-2,20 L-34,40", "none", 3, "rgba(0,0,0,.35)")),
    at(x, y, s, r));
  P.brain = (id, x, y, s = 1, o = {}) => {
    const col = o.col || C.pink;
    const face = o.face
      ? circ(-40, -10, 16, C.white, 5) + circ(40, -10, 16, C.white, 5) +
        g(`${id}-pupils`, circ(-40, -8, 7, C.ink, 0) + circ(40, -8, 7, C.ink, 0)) +
        `<g id="${id}-m-smile">${path("M-24,30 Q0,50 24,30", "none", 6)}</g>` +
        `<g id="${id}-m-flat" opacity="0">${path("M-18,36 L18,36", "none", 6)}</g>` +
        `<g id="${id}-m-o" opacity="0">${ell(0, 36, 10, 13, C.mouth, 5)}</g>`
      : "";
    return g(null, g(id,
      path("M-170,40 Q-200,-40 -150,-100 Q-140,-170 -60,-170 Q-10,-210 50,-176 Q130,-190 160,-120 Q215,-70 180,10 Q190,80 120,100 Q90,140 30,120 Q-30,150 -80,116 Q-150,120 -170,40 Z", col, 8) +
      `<g id="${id}-folds">` +
      path("M-120,-90 Q-80,-60 -100,-20 M-40,-150 Q-20,-110 -50,-80 M40,-150 Q60,-110 30,-80 M110,-110 Q80,-70 120,-40 M-130,30 Q-90,20 -70,60 M60,40 Q100,20 130,60 M-20,60 Q10,30 30,80", "none", 6, o.fold || C.pinkDark) +
      `</g>` + face),
      at(x, y, s));
  };
  /** side-view brain with cerebellum + somatosensory strip as separately addressable regions */
  P.brainSide = (id, x, y, s = 1) => g(null, g(id,
    // cerebellum (back-bottom, which is screen-right here: face looks left)
    g(`${id}-cereb`, path("M90,40 Q170,30 190,80 Q196,130 130,134 Q80,132 70,96 Z", "#E78F9F", 7) +
      path("M92,70 Q140,60 180,84 M88,96 Q140,90 182,110 M100,120 Q140,116 166,126", "none", 4, C.pinkDark)) +
    path("M60,120 Q60,180 40,220 L84,222 Q96,170 100,128", "#F0B9C2", 7) + // brainstem
    path("M-200,10 Q-220,-90 -140,-150 Q-60,-210 40,-196 Q150,-186 196,-110 Q230,-40 190,50 Q150,70 100,50 Q60,90 0,80 Q-80,100 -150,70 Q-196,56 -200,10 Z", C.pink, 8) +
    g(`${id}-strip`, path("M-10,-196 Q20,-120 0,-40 Q-6,20 20,76", "none", 26, C.pink, `stroke-opacity="1"`)) +
    path("M-150,-100 Q-110,-80 -130,-40 M-90,-160 Q-70,-120 -100,-90 M60,-170 Q80,-130 50,-100 M120,-120 Q100,-80 140,-60 M-150,20 Q-110,10 -80,40 M70,-20 Q110,-40 150,0 M-60,-20 Q-30,-50 -10,-10", "none", 6, C.pinkDark)),
    at(x, y, s));
  P.clock = (id, x, y, s = 1) => g(null, g(id,
    circ(0, 0, 90, C.white, 8) + Array.from({ length: 12 }, (_, i) => {
      const a = (i / 12) * Math.PI * 2;
      return line(Math.sin(a) * 70, -Math.cos(a) * 70, Math.sin(a) * 80, -Math.cos(a) * 80, 5);
    }).join("") +
    g(`${id}-hr`, line(0, 0, 0, -42, 8)) + g(`${id}-min`, line(0, 0, 0, -64, 6)) + circ(0, 0, 7, C.ink, 0)),
    at(x, y, s));
  P.stopwatch = (id, x, y, s = 1) => g(null, g(id,
    rect(-18, -128, 36, 26, C.gray, 6, 6) + line(70, -78, 86, -94, 10) +
    circ(0, 0, 100, C.white, 8) + circ(0, 0, 84, "none", 3, C.gray) +
    g(`${id}-hand`, line(0, 0, 0, -74, 6, C.red)) + circ(0, 0, 8, C.ink, 0)),
    at(x, y, s));
  P.envelope = (id, x, y, s = 1, col = C.white) => g(null, g(id,
    rect(-80, -52, 160, 104, col, 8, 7) + path("M-78,-48 L0,14 L78,-48", "none", 6)),
    at(x, y, s));
  P.bubble = (id, x, y, w, h, inner = "", tail = "left", fill = C.white) => {
    const tx = tail === "left" ? -w / 2 + 40 : w / 2 - 40;
    const td = tail === "left" ? -30 : 30;
    return g(null, g(id,
      rect(-w / 2, -h / 2, w, h, fill, 40, 7) +
      path(`M${tx - 18},${h / 2 - 4} L${tx + td},${h / 2 + 44} L${tx + 22},${h / 2 - 4}`, fill, 7) +
      `<rect x="${tx - 22}" y="${h / 2 - 12}" width="48" height="10" fill="${fill}"/>` + inner),
      at(x, y));
  };
  P.thought = (id, x, y, w, h, inner = "", fill = C.white) => g(null, g(id,
    ell(0, 0, w / 2, h / 2, fill, 7) + circ(-w / 4, h / 2 + 30, 18, fill, 6) + circ(-w / 4 - 30, h / 2 + 70, 10, fill, 5) + inner),
    at(x, y));
  P.check = (id, x, y, s = 1, col = C.green) => g(null, g(id, path("M-40,0 L-10,32 L48,-40", "none", 16, col)), at(x, y, s));
  P.cross = (id, x, y, s = 1, col = C.red) => g(null, g(id, path("M-40,-40 L40,40 M40,-40 L-40,40", "none", 16, col)), at(x, y, s));
  P.question = (id, x, y, s = 1, col = C.ink) => g(null, g(id, text(0, 0, "?", 220, col, "middle", `font-weight="700"`, FONT2)), at(x, y, s));
  P.exclaim = (id, x, y, s = 1, col = C.red) => g(null, g(id, text(0, 0, "!", 220, col, "middle", "", FONT2)), at(x, y, s));
  P.arrow = (id, x1, y1, x2, y2, w = 7, col = C.ink, bend = 0) => {
    const mx = (x1 + x2) / 2 + bend, my = (y1 + y2) / 2 - Math.abs(bend) * 0.4;
    const a = Math.atan2(y2 - my, x2 - mx);
    const h = 26;
    const hx1 = x2 - h * Math.cos(a - 0.5), hy1 = y2 - h * Math.sin(a - 0.5);
    const hx2 = x2 - h * Math.cos(a + 0.5), hy2 = y2 - h * Math.sin(a + 0.5);
    return g(id, path(`M${x1},${y1} Q${mx},${my} ${x2},${y2}`, "none", w, col, `class="draw"`) +
      path(`M${hx1},${hy1} L${x2},${y2} L${hx2},${hy2}`, "none", w, col));
  };
  P.speaker = (id, x, y, s = 1) => g(null, g(id,
    path("M-60,-30 L-24,-30 L20,-70 L20,70 L-24,30 L-60,30 Z", C.gray2, 7) +
    g(`${id}-w1`, path("M44,-30 Q62,0 44,30", "none", 8)) +
    g(`${id}-w2`, path("M66,-56 Q98,0 66,56", "none", 8)) +
    g(`${id}-w3`, path("M88,-82 Q134,0 88,82", "none", 8))),
    at(x, y, s));
  P.knob = (id, x, y, s = 1, label = "VOLUME") => g(null, g(id,
    circ(0, 0, 110, C.paper2, 7) + Array.from({ length: 9 }, (_, i) => {
      const a = (-135 + i * 33.75) * Math.PI / 180;
      return line(Math.sin(a) * 124, -Math.cos(a) * 124, Math.sin(a) * 140, -Math.cos(a) * 140, 5);
    }).join("") +
    g(`${id}-dial`, circ(0, 0, 80, C.gray2, 7) + line(0, -20, 0, -66, 9, C.red)) +
    text(0, 175, label, 46)),
    at(x, y, s));
  P.meter = (id, x, y, h = 360, label = "", col = C.red) => g(null, g(id,
    rect(-40, -h, 80, h, C.white, 18, 7) +
    `<g id="${id}-fill">${rect(-30, -h + 10, 60, h - 20, col, 12, 0)}</g>` +
    rect(-40, -h, 80, h, "none", 18, 7) + text(0, 50, label, 44)),
    at(x, y));
  P.robot = (id, x, y, s = 1, col = "#9FB7C9") => g(null, g(id,
    line(0, -190, 0, -230, 6) + circ(0, -236, 12, C.red, 5) +
    rect(-90, -190, 180, 140, col, 26, 7) + rect(-62, -160, 124, 76, "#2F3A4A", 16, 5) +
    g(`${id}-eyes`, circ(-28, -122, 13, "#7CF0E0", 0) + circ(28, -122, 13, "#7CF0E0", 0)) +
    rect(-70, -40, 140, 130, col, 20, 7) + circ(0, 20, 16, C.yellow, 5) +
    g(`${id}-armL`, line(-70, -20, -130, 50, 9) + circ(-134, 56, 14, C.gray, 5)) +
    g(`${id}-armR`, line(70, -20, 130, 50, 9) + circ(134, 56, 14, C.gray, 5)) +
    line(-34, 90, -34, 150, 9) + line(34, 90, 34, 150, 9)),
    at(x, y, s));
  P.cricket = (id, x, y, s = 1) => g(null, g(id,
    // back legs
    path("M40,10 L120,-60 L170,60", "none", 9, "#3E5A2A") + path("M30,20 L90,-30 L130,70", "none", 9, "#3E5A2A") +
    // front legs (where its ears are!)
    g(`${id}-legF`, path("M-60,20 L-90,60 L-120,70", "none", 8, "#3E5A2A") + ell(-90, 56, 8, 5, C.yellow, 3)) +
    path("M-20,20 L-30,70 L-50,80", "none", 8, "#3E5A2A") +
    ell(20, 0, 110, 46, "#6E9B3E", 7) +
    g(`${id}-wings`, path("M-40,-20 Q40,-70 140,-20 Q60,10 -40,-4 Z", "#87B354", 6) + path("M-10,-24 Q50,-50 120,-22", "none", 3, "#3E5A2A")) +
    circ(-100, -10, 40, "#6E9B3E", 7) + circ(-112, -20, 12, C.white, 4) + circ(-114, -20, 6, C.ink, 0) +
    path("M-120,-46 Q-180,-140 -120,-200 M-108,-48 Q-140,-150 -60,-200", "none", 4, "#3E5A2A")),
    at(x, y, s));
  P.rat = (id, x, y, s = 1) => g(null, g(id,
    path("M110,20 Q200,40 230,-20 Q240,-50 220,-60", "none", 7, "#D99BA5") +
    ell(30, 0, 110, 66, "#C9C3BC", 7) +
    circ(-70, -30, 54, "#C9C3BC", 7) + circ(-58, -86, 26, C.pink, 6) + circ(-104, -78, 22, C.pink, 6) +
    circ(-86, -36, 8, C.ink, 0) + circ(-122, -10, 9, C.pinkDark, 0) +
    g(`${id}-m`, path("M-110,8 Q-96,20 -84,8", "none", 4)) +
    path("M-126,-16 L-170,-30 M-126,-10 L-172,-6 M-126,-4 L-166,14", "none", 3) +
    line(-30, 56, -40, 76, 7) + line(70, 56, 80, 76, 7)),
    at(x, y, s));
  P.baby = (id, x, y, s = 1) => g(null, g(id,
    ell(0, 60, 70, 60, "#BFE3F7", 7) +
    circ(0, -40, 58, C.white, 6) + path("M-6,-98 Q4,-120 16,-104", "none", 5) +
    g(`${id}-eyes`, path("M-30,-46 Q-20,-58 -10,-46 M10,-46 Q20,-58 30,-46", "none", 5)) +
    g(`${id}-m`, path("M-20,-18 Q0,10 20,-18 Z", C.mouth, 5)) +
    ell(-34, -24, 9, 6, C.pink, 0) + ell(34, -24, 9, 6, C.pink, 0)),
    at(x, y, s));
  P.heart = (id, x, y, s = 1, col = C.red) => g(null, g(id,
    path("M0,30 Q-60,-10 -40,-40 Q-20,-62 0,-36 Q20,-62 40,-40 Q60,-10 0,30 Z", col, 5)), at(x, y, s));
  P.laptop = (id, x, y, s = 1) => g(null, g(id,
    rect(-120, -150, 240, 150, "#56627A", 12, 7) + rect(-104, -136, 208, 122, "#BFE8F6", 6, 0) +
    path("M-160,0 L160,0 L180,26 L-180,26 Z", C.gray, 7)), at(x, y, s));
  P.ball = (id, x, y, s = 1) => g(null, g(id,
    circ(0, 0, 40, C.red, 6) + path("M-36,-14 Q0,10 36,-14 M-30,22 Q0,0 30,22", "none", 4, C.white)), at(x, y, s));
  P.mri = (id, x, y, s = 1) => g(null, g(id,
    rect(-300, -260, 360, 520, "#E8EDF1", 60, 8) + circ(-120, 0, 120, "#B9C6D2", 8) + circ(-120, 0, 92, "#56627A", 6) +
    rect(-120, -20, 520, 50, "#DCE3E8", 14, 7) + rect(-80, 30, 460, 120, "#C3CDD6", 12, 7) +
    rect(-250, -230, 60, 20, C.teal, 6, 0)), at(x, y, s));
  P.monitor = (id, x, y, s = 1, inner = "") => g(null, g(id,
    rect(-260, -190, 520, 340, "#56627A", 22, 8) + rect(-236, -166, 472, 292, "#1E2633", 10, 0) + inner +
    rect(-40, 150, 80, 50, C.gray, 4, 7) + rect(-120, 196, 240, 22, C.gray, 8, 7)), at(x, y, s));
  P.table = (id, x, y, w = 600) => g(id,
    rect(x - w / 2, y, w, 30, "#C08A55", 6, 7) + line(x - w / 2 + 40, y + 30, x - w / 2 + 40, y + 200, 10) +
    line(x + w / 2 - 40, y + 30, x + w / 2 - 40, y + 200, 10));
  P.lightbulb = (id, x, y, s = 1) => g(null, g(id,
    g(`${id}-glow`, circ(0, -20, 110, C.yellow, 0, C.ink, `opacity=".35"`)) +
    path("M-56,-30 Q-60,-110 0,-114 Q60,-110 56,-30 Q40,0 34,30 L-34,30 Q-40,0 -56,-30 Z", "#FFF3B0", 7) +
    rect(-34, 30, 68, 40, C.gray, 6, 6) + path("M-16,-10 L-6,-40 L6,-10 L16,-40", "none", 4)), at(x, y, s));
  P.sign = (id, x, y, w, h, label, fill = C.white, size = 64, col = C.ink) => g(null, g(id,
    rect(-w / 2, -h / 2, w, h, fill, 16, 7) + text(0, 4, label, size, col)), at(x, y));
  P.box = (id, x, y, w, h, label, fill = "#D9A86C") => g(null, g(id,
    path(`M${-w / 2},${-h / 2} L${w / 2},${-h / 2} L${w / 2 - 20},${h / 2} L${-w / 2 + 20},${h / 2} Z`, fill, 8) +
    rect(-w / 2 - 14, -h / 2 - 30, w + 28, 40, fill, 8, 8) + text(0, 30, label, 44)), at(x, y));
  P.spider = (id, x, y, s = 1) => g(null, g(id,
    [-1, 1].map((d) => [-30, -10, 10, 30].map((yy) => path(`M0,${yy * 0.6} Q${d * 46},${yy - 30} ${d * 66},${yy + 16}`, "none", 5)).join("")).join("") +
    circ(0, 0, 28, C.ink, 0) + circ(-9, -6, 6, C.white, 0) + circ(9, -6, 6, C.white, 0)), at(x, y, s));
  P.flag = (id, x, y, s = 1, col = C.red) => g(null, g(id,
    line(0, 0, 0, -200, 8) + path("M0,-200 Q50,-220 100,-196 Q140,-176 120,-150 Q70,-130 0,-140 Z", col, 6)), at(x, y, s));
  P.mute = (id, x, y, s = 1) => g(null, g(id,
    path("M-60,-30 L-24,-30 L20,-70 L20,70 L-24,30 L-60,30 Z", C.gray2, 7) + path("M50,-30 L110,30 M110,-30 L50,30", "none", 10, C.red)), at(x, y, s));
  P.star = (id, x, y, s = 1, col = C.yellow) => g(null, g(id,
    path("M0,-50 L14,-16 L50,-14 L22,8 L32,44 L0,24 L-32,44 L-22,8 L-50,-14 L-14,-16 Z", col, 5)), at(x, y, s));
  P.neuron = (id, x, y, s = 1, col = C.purple) => g(null, g(id,
    path("M-200,0 L120,0", "none", 12, col) + path("M120,0 L170,-40 M120,0 L176,0 M120,0 L170,40", "none", 8, col) +
    path("M-200,0 L-250,-50 M-200,0 L-260,10 M-200,0 L-240,56", "none", 8, col) + circ(-200, 0, 34, col, 7) +
    g(`${id}-pulse`, circ(-200, 0, 16, C.yellow, 4))), at(x, y, s));
  P.tumbleweed = (id, x, y, s = 1) => g(null, g(id,
    circ(0, 0, 60, "none", 6, "#9A7A4A") + path("M-50,-20 Q0,40 50,-30 M-40,30 Q0,-50 44,30 M-58,4 Q0,-10 58,8 M-20,-56 Q10,0 -10,58", "none", 5, "#9A7A4A")),
    at(x, y, s));
  P.car = (id, x, y, s = 1) => g(null, g(id,
    path("M-380,40 L-380,-60 Q-360,-90 -300,-96 L-200,-200 Q-180,-214 -140,-214 L170,-214 Q210,-212 230,-190 L320,-96 Q380,-90 390,-50 L390,40 Z M-180,-190 L-20,-190 L-20,-100 L-180,-100 Z M10,-190 L190,-190 L190,-100 L10,-100 Z", C.blue, 9, C.ink, `fill-rule="evenodd"`) +
    rect(-180, -190, 160, 90, "rgba(207,234,244,.3)", 10, 7) + rect(10, -190, 180, 90, "rgba(207,234,244,.3)", 10, 7) +
    circ(-240, 50, 64, "#3A3A3A", 8) + circ(-240, 50, 26, C.gray, 6) + circ(250, 50, 64, "#3A3A3A", 8) + circ(250, 50, 26, C.gray, 6)),
    at(x, y, s));
  P.big_ben = (id, x, y, s = 1) => g(null, g(id,
    rect(-50, -260, 100, 380, "#E2C48B", 4, 7) + path("M-60,-260 L0,-360 L60,-260 Z", "#B6915A", 7) +
    circ(0, -190, 36, C.white, 6) + line(0, -190, 0, -214, 5) + line(0, -190, 16, -190, 5) +
    line(-30, -120, 30, -120, 4) + line(-30, -60, 30, -60, 4) + line(-30, 0, 30, 0, 4) + line(-30, 60, 30, 60, 4)),
    at(x, y, s));
  P.calendar = (id, x, y, s = 1, label = "1971") => g(null, g(id,
    rect(-150, -150, 300, 300, C.white, 18, 8) + rect(-150, -150, 300, 80, C.red, 18, 8) +
    circ(-80, -150, 12, C.ink, 0) + circ(80, -150, 12, C.ink, 0) +
    `<g id="${id}-label">${text(0, 40, label, 120)}</g>`), at(x, y, s));
  P.magnifier = (id, x, y, s = 1) => g(null, g(id,
    line(60, 60, 150, 150, 22, "#7A5236") + circ(0, 0, 90, "rgba(200,235,250,.5)", 10)), at(x, y, s));
  P.puppetBar = (id, x, y, s = 1) => g(null, g(id,
    rect(-160, -10, 320, 20, "#B6915A", 6, 6) + rect(-10, -120, 20, 240, "#B6915A", 6, 6)), at(x, y, s));
  P.scale = (id, x, y, s = 1) => g(null, g(id,
    line(0, 0, 0, -260, 9) + path("M-80,0 L80,0", "none", 10) +
    g(`${id}-beam`, line(-220, -260, 220, -260, 10) +
      g(`${id}-panL`, line(-220, -260, -220, -170, 4) + path("M-290,-170 L-150,-170 Q-160,-120 -220,-120 Q-280,-120 -290,-170 Z", C.yellow, 6)) +
      g(`${id}-panR`, line(220, -260, 220, -170, 4) + path("M150,-170 L290,-170 Q280,-120 220,-120 Q160,-120 150,-170 Z", C.yellow, 6))) +
    circ(0, -260, 14, C.ink, 0)), at(x, y, s));
  P.eyeBig = (id, x, y, s = 1) => g(null, g(id,
    path("M-420,0 Q0,-300 420,0 Q0,300 -420,0 Z", C.white, 12) +
    g(`${id}-iris`, circ(0, 0, 150, C.teal, 10) + circ(0, 0, 70, C.ink, 0) + circ(-46, -50, 26, C.white, 0)) +
    `<path d="M-420,0 Q0,-300 420,0" fill="none" stroke="${C.ink}" stroke-width="14"/>`), at(x, y, s));
  P.cloud = (id, x, y, s = 1, col = C.white) => g(null, g(id,
    path("M-120,40 Q-170,40 -160,0 Q-150,-40 -100,-34 Q-90,-90 -20,-80 Q30,-120 80,-70 Q140,-80 140,-20 Q180,0 150,40 Z", col, 6)), at(x, y, s));
  P.sun = (id, x, y, s = 1) => g(null, g(id,
    circ(0, 0, 70, C.yellow, 7) + Array.from({ length: 10 }, (_, i) => {
      const a = (i / 10) * Math.PI * 2;
      return line(Math.cos(a) * 92, Math.sin(a) * 92, Math.cos(a) * 124, Math.sin(a) * 124, 7, "#E9A825");
    }).join("")), at(x, y, s));
  P.plant = (id, x, y, s = 1) => g(null, g(id,
    path("M-40,0 L40,0 L30,70 L-30,70 Z", "#D9744A", 6) + path("M0,0 Q-10,-60 -60,-90 M0,0 Q10,-80 50,-110 M0,0 Q0,-60 0,-130", "none", 6, "#3E7A3A") +
    ell(-60, -96, 26, 12, C.green, 5) + ell(54, -114, 26, 12, C.green, 5) + ell(0, -136, 14, 26, C.green, 5)), at(x, y, s));
  P.window = (id, x, y, w = 260, h = 220, sky = C.sky) => g(id,
    rect(x - w / 2, y - h / 2, w, h, sky, 6, 9) + line(x, y - h / 2, x, y + h / 2, 7) + line(x - w / 2, y, x + w / 2, y, 7));
  P.lamp = (id, x, y, s = 1) => g(null, g(id,
    path("M-60,-160 L60,-160 L84,-60 L-84,-60 Z", "#FBE7A3", 7) + line(0, -60, 0, 80, 8) + rect(-50, 80, 100, 18, C.ink, 6, 0)), at(x, y, s));
  P.chair = (id, x, y, s = 1, col = C.teal) => g(null, g(id,
    rect(-90, -200, 30, 200, col, 10, 7) + rect(-90, -20, 180, 30, col, 10, 7) +
    line(-76, 10, -76, 110, 9) + line(76, 10, 76, 110, 9)), at(x, y, s));
  P.mirror = (id, x, y, w = 340, h = 600) => g(id,
    rect(x - w / 2 - 18, y - h / 2 - 18, w + 36, h + 36, "#B6915A", 26, 8) + rect(x - w / 2, y - h / 2, w, h, "#DDF1F8", 14, 6) +
    path(`M${x - w / 2 + 40},${y - h / 2 + 60} L${x - w / 2 + 110},${y - h / 2 + 20} M${x - w / 2 + 40},${y - h / 2 + 130} L${x - w / 2 + 170},${y - h / 2 + 40}`, "none", 8, "rgba(255,255,255,.9)"));


  // open palm facing viewer, fingers up; wrist at (0, 200)
  P.palm = (id, x, y, s = 1, skin = "#FFE9D6", sleeveCol = null) => g(null, g(id,
    (sleeveCol ? rect(-110, 170, 220, 160, sleeveCol, 20, 7) : "") +
    path("M-100,180 L-110,0 Q-112,-40 -96,-60 L-96,-200 Q-96,-226 -72,-226 Q-50,-226 -50,-200 L-48,-110 L-46,-250 Q-46,-276 -22,-276 Q2,-276 2,-250 L2,-120 L6,-262 Q6,-288 30,-288 Q54,-288 54,-262 L52,-116 L58,-230 Q58,-254 82,-254 Q104,-254 104,-230 L100,-40 Q150,-90 176,-66 Q196,-48 172,-14 Q120,60 96,110 L90,180 Z", skin, 7) +
    path("M-60,40 Q0,80 60,30 M-40,-20 Q10,0 50,-30", "none", 4, "#D9A889")),
    at(x, y, s));
  // a stick with a soft foam tip (tip at origin, handle going down-right)
  P.foamStick = (id, x, y, s = 1, r = 0) => g(null, g(id,
    line(0, 0, 0, 300, 14, C.ink) + line(0, 0, 0, 300, 8, "#C08A55") + rect(-34, -60, 68, 90, C.yellow, 30, 7) +
    circ(-10, -30, 5, "#E2A92C", 0) + circ(12, -10, 5, "#E2A92C", 0) + circ(-6, 6, 4, "#E2A92C", 0)),
    at(x, y, s, r));
  P.crystal = (id, x, y, s = 1) => g(null, g(id,
    g(`${id}-glow`, circ(0, 0, 230, "#C9B5F2", 0, C.ink, `opacity=".5"`)) +
    path("M-140,170 L140,170 L110,120 L-110,120 Z", "#8A5A3A", 7) +
    circ(0, 0, 150, "#E7DCFB", 8) + path("M-90,-70 Q-60,-110 -20,-120", "none", 10, "rgba(255,255,255,.9)")),
    at(x, y, s));
  P.hat = (id, x, y, s = 1, col = "#6B5444") => g(null, g(id,
    path("M-120,0 Q0,-30 120,0 Q60,20 -120,0 Z", col, 6) + path("M-70,-10 Q-70,-90 0,-96 Q70,-90 70,-10 Z", col, 6) +
    path("M-70,-30 Q0,-44 70,-30", "none", 10, C.ink)),
    at(x, y, s));


  // ---------- supermarket props ----------
  // shopping cart, wheels on the floor at (0,0); handle at left
  P.cart = (id, x, y, s = 1, flip = 1) => g(null, g(id, g(null,
    path("M-250,-300 L-210,-300 L-170,-60 L170,-60 L210,-250 L-200,-250", "none", 10) +
    path("M-196,-250 L196,-250 L166,-80 L-166,-80 Z", "rgba(200,220,235,.35)", 0) +
    Array.from({ length: 7 }, (_, i) => line(-170 + i * 56, -246, -150 + i * 50, -80, 4, "#8A97A3")).join("") +
    line(-190, -190, 200, -190, 4, "#8A97A3") + line(-180, -130, 190, -130, 4, "#8A97A3") +
    line(-170, -60, -150, -10, 8) + line(170, -60, 150, -10, 8) + line(-150, -10, 150, -10, 8) +
    `<g id="${id}-load"></g>` +
    circ(-130, 18, 22, "#3A3A3A", 6) + circ(130, 18, 22, "#3A3A3A", 6), flip === -1 ? "scale(-1 1)" : "")),
    at(x, y, s));
  /** product: kind = box | can | bottle | bag | jar | milk, label text optional */
  P.product = (id, x, y, s = 1, kind = "box", col = C.red, label = "") => {
    let d = "";
    if (kind === "box") d = rect(-45, -140, 90, 140, col, 8, 6) + rect(-30, -110, 60, 50, C.white, 6, 0) + (label ? text(0, -86, label, 26) : "");
    else if (kind === "can") d = rect(-34, -90, 68, 90, col, 10, 6) + rect(-34, -64, 68, 34, C.white, 0, 0) + line(-34, -64, 34, -64, 4) + line(-34, -30, 34, -30, 4) + (label ? text(0, -46, label, 22) : "");
    else if (kind === "bottle") d = path("M-30,0 L-30,-110 Q-30,-140 -12,-150 L-12,-190 L12,-190 L12,-150 Q30,-140 30,-110 L30,0 Z", col, 6) + rect(-24, -100, 48, 44, C.paper, 4, 0) + (label ? text(0, -78, label, 20) : "");
    else if (kind === "bag") d = path("M-55,0 L-60,-120 L-45,-130 L45,-130 L60,-120 L55,0 Z", col, 6) + path("M-45,-130 L-40,-112 L-30,-130 L-20,-112 L-10,-130 L0,-112 L10,-130 L20,-112 L30,-130 L40,-112 L45,-130", "none", 4) + (label ? text(0, -62, label, 28, C.white) : "");
    else if (kind === "jar") d = rect(-36, -100, 72, 100, col, 14, 6) + rect(-40, -116, 80, 22, C.gray, 6, 6);
    else if (kind === "milk") d = path("M-50,0 L-50,-150 L-20,-190 L50,-190 L50,0 Z", C.white, 6) + path("M-50,-150 L20,-150 L50,-190 M20,-150 L20,0", "none", 5) + rect(-40, -110, 52, 60, C.blue, 6, 0) + text(-14, -78, "MILK", 18, C.white);
    return g(null, g(id, d), at(x, y, s));
  };
  /** shelf unit: rows of products. rows = array of {y, items:[[kind,col,label]...]} */
  P.shelf = (id, x, y, w, h, rows = 4, seed = 1, colors = null) => {
    const r = rng(seed);
    const pal = colors || [C.red, C.blue, C.yellow, C.green, C.orange, C.purple, C.teal, C.pink];
    const kinds = ["box", "can", "bottle", "bag", "jar"];
    let d = rect(x, y, w, h, "#E7E1D6", 6, 8);
    for (let i = 0; i < rows; i++) {
      const sy = y + ((i + 1) * h) / rows;
      const k = kinds[Math.floor(r() * kinds.length)];
      const n = Math.floor(w / 110);
      for (let j = 0; j < n; j++) {
        const px = x + 60 + j * ((w - 120) / Math.max(1, n - 1));
        const sc = (h / rows) / 200;
        d += P.product(null, px, sy - 8, sc, k, pal[Math.floor(r() * pal.length)]);
      }
      d += rect(x, sy - 8, w, 18, "#B9AE9C", 3, 6);
    }
    return g(id, d);
  };
  P.priceTag = (id, x, y, s = 1, price = "$2.99", col = C.yellow, rot = 0) => g(null, g(id,
    path("M-120,-60 L90,-60 L140,0 L90,60 L-120,60 Z", col, 7) + circ(100, 0, 10, C.white, 5) + text(-14, 6, price, 64)),
    at(x, y, s, rot));
  P.storefront = (id, x, y, s = 1) => g(null, g(id,
    rect(-600, -420, 1200, 440, "#F2E6CF", 10, 9) + rect(-640, -500, 1280, 100, C.red, 14, 9) +
    text(0, -446, "SUPERMARKET", 72, C.white) +
    Array.from({ length: 6 }, (_, i) => path(`M${-640 + i * 213},-400 L${-640 + (i + 1) * 213},-400 L${-640 + (i + 1) * 213 - 20},-340 Q${-640 + i * 213 + 106},-310 ${-640 + i * 213 + 20},-340 Z`, i % 2 ? C.white : C.red, 6)).join("") +
    rect(-170, -280, 340, 300, "#BFE3F1", 6, 8) + line(0, -280, 0, 20, 7) +
    rect(-540, -280, 300, 200, "#BFE3F1", 6, 8) + rect(240, -280, 300, 200, "#BFE3F1", 6, 8)),
    at(x, y, s));
  P.chips = (id, x, y, s = 1, col = C.orange) => P.product(id, x, y, s, "bag", col, "CHIPS");
  P.candle = (id, x, y, s = 1) => g(null, g(id,
    rect(-40, -120, 80, 120, "#F3D1E0", 10, 6) + line(0, -120, 0, -146, 5) +
    path("M0,-192 Q-18,-160 0,-146 Q18,-160 0,-192 Z", C.yellow, 4)), at(x, y, s));
  P.bread = (id, x, y, s = 1) => g(null, g(id,
    path("M-110,0 L-110,-60 Q-110,-120 0,-122 Q110,-120 110,-60 L110,0 Z", "#E2A85A", 7) +
    path("M-60,-100 L-40,-70 M-10,-110 L10,-78 M40,-102 L60,-72", "none", 5, "#B3772F")), at(x, y, s));
  P.apple = (id, x, y, s = 1, col = C.red) => g(null, g(id,
    path("M0,-70 Q-60,-90 -66,-30 Q-64,30 0,40 Q64,30 66,-30 Q60,-90 0,-70 Z", col, 6) + line(0, -70, 6, -96, 6) +
    ell(24, -92, 20, 9, C.green, 4)), at(x, y, s));
  P.banana = (id, x, y, s = 1) => g(null, g(id,
    path("M-90,-40 Q0,60 100,-50 Q90,10 0,20 Q-70,10 -90,-40 Z", C.yellow, 6)), at(x, y, s));
  P.flowers = (id, x, y, s = 1) => g(null, g(id,
    path("M-40,0 L40,0 L30,-80 L-30,-80 Z", C.teal, 6) +
    [[-40, -170, C.pink], [0, -200, C.red], [40, -165, C.yellow], [-10, -140, C.purple]].map(([a, b, c]) =>
      line(0, -80, a, b, 4, "#3E7A3A") + circ(a, b, 22, c, 5) + circ(a, b, 7, C.yellow, 0)).join("")), at(x, y, s));
  P.wine = (id, x, y, s = 1, col = "#7A1E3A", label = "") => P.product(id, x, y, s, "bottle", col, label);
  P.note = (id, x, y, s = 1, col = C.ink) => g(null, g(id,
    ell(-14, 30, 22, 16, col, 0) + line(6, 30, 6, -50, 7, col) + path("M6,-50 Q40,-40 34,-10", "none", 7, col)), at(x, y, s));
  P.card = (id, x, y, s = 1, col = C.teal, label = "LOYALTY") => g(null, g(id,
    rect(-160, -100, 320, 200, col, 20, 7) + rect(-160, -60, 320, 34, C.ink, 0, 0) + text(-60, 50, label, 40, C.white) +
    rect(70, 20, 60, 44, C.yellow, 8, 4)), at(x, y, s));
  P.dress = (id, x, y, s = 1, col = C.purple) => g(null, g(id,
    path("M-40,-200 L-60,-130 L-40,-100 L-110,60 Q0,90 110,60 L40,-100 L60,-130 L40,-200 Q0,-170 -40,-200 Z", col, 7) +
    path("M-40,-200 L-60,-240 M40,-200 L60,-240", "none", 5)), at(x, y, s));
  P.receipt = (id, x, y, s = 1, lines = 10, total = "") => {
    let d = path(`M-110,-${lines * 34 + 60} L110,-${lines * 34 + 60} L110,0 L90,20 L70,0 L50,20 L30,0 L10,20 L-10,0 L-30,20 L-50,0 L-70,20 L-90,0 L-110,20 Z`, C.white, 6);
    for (let i = 0; i < lines; i++) d += line(-80, -lines * 34 - 20 + i * 34, 30 + ((i * 37) % 50), -lines * 34 - 20 + i * 34, 5, C.gray) + line(60, -lines * 34 - 20 + i * 34, 85, -lines * 34 - 20 + i * 34, 5, C.gray);
    if (total) d += text(0, -24, total, 40, C.red);
    return g(null, g(id, d), at(x, y, s));
  };
  P.candy = (id, x, y, s = 1, col = C.red) => g(null, g(id,
    rect(-70, -26, 140, 52, col, 8, 6) + path("M-70,-26 L-96,-38 L-96,38 L-70,26 M70,-26 L96,-38 L96,38 L70,26", C.gray2, 5) + text(0, 4, "YUM", 28, C.white)), at(x, y, s));
  P.list = (id, x, y, s = 1, items = ["milk"]) => g(null, g(id,
    rect(-150, -220, 300, 440, "#FFF8D6", 10, 7) + path("M-150,-170 L150,-170", "none", 3, C.red) +
    items.map((t, i) => text(-110, -120 + i * 70, "□ " + t, 50, C.ink, "start", "", FONT2)).join("")), at(x, y, s));
  P.checkout = (id, x, y, s = 1) => g(null, g(id,
    rect(-420, -160, 840, 160, "#A9B8C4", 10, 8) + rect(-420, -190, 840, 40, "#56627A", 8, 8) +
    rect(160, -330, 200, 150, "#56627A", 12, 8) + rect(180, -310, 160, 90, "#7CF0E0", 6, 0) + text(260, -264, "$47.83", 44) +
    line(-300, -190, -300, -230, 6)), at(x, y, s));
  P.pilotCap = (id, x, y, s = 1) => g(null, g(id,
    path("M-110,10 Q-110,-90 0,-96 Q110,-90 110,10 Z", "#2D3460", 7) + path("M-130,10 L130,10 L150,34 L-150,34 Z", C.ink, 0) +
    circ(0, -50, 20, C.yellow, 5)), at(x, y, s));
  P.scaleWeight = (id, x, y, s = 1, label = "500 g") => g(null, g(id,
    rect(-130, -40, 260, 60, C.gray2, 12, 7) + rect(-90, -90, 180, 50, "#1E2633", 8, 6) + text(0, -64, label, 40, "#7CF0E0")), at(x, y, s));

  // ---------- backgrounds ----------
  const BG = {};
  BG.paper = (id = "") => `<rect ${id ? `id="${id}"` : ""} x="-200" y="-200" width="2320" height="1480" fill="${C.paper}"/>`;
  BG.flat = (col) => `<rect x="-200" y="-200" width="2320" height="1480" fill="${col}"/>`;
  BG.room = (o = {}) => {
    const wall = o.wall || C.wall, floor = o.floor || C.floor, fy = o.fy || 780;
    return `<rect x="-200" y="-200" width="2320" height="${fy + 200}" fill="${wall}"/>` +
      `<rect x="-200" y="${fy}" width="2320" height="${1280 - fy}" fill="${floor}"/>` +
      line(-200, fy, 2120, fy, 7) +
      Array.from({ length: 9 }, (_, i) => line(-200, fy + 60 + i * 70, 2120, fy + 60 + i * 70, 3, "rgba(0,0,0,.12)")).join("") +
      line(-200, fy - 30, 2120, fy - 30, 4, "rgba(0,0,0,.12)");
  };
  BG.outdoor = (o = {}) => {
    const hy = o.hy || 720;
    return `<rect x="-200" y="-200" width="2320" height="${hy + 200}" fill="${o.sky || C.sky}"/>` +
      `<rect x="-200" y="${hy}" width="2320" height="${1280 - hy}" fill="${o.ground || C.grass}"/>` +
      path(`M-200,${hy} Q480,${hy - 30} 960,${hy} T2120,${hy}`, o.ground || C.grass, 7);
  };
  BG.night = () =>
    `<rect x="-200" y="-200" width="2320" height="1480" fill="${C.night}"/>` +
    Array.from({ length: 40 }, (_, i) => {
      const r = rng(i + 11);
      return circ(r() * 1920, r() * 700, 2 + r() * 3, "#FFF7D6", 0);
    }).join("");
  BG.lab = (o = {}) => BG.room({ wall: o.wall || "#DCEBEE", floor: o.floor || "#9FB3BD", fy: o.fy || 800 }) +
    Array.from({ length: 6 }, (_, i) => rect(80 + i * 300, 120, 200, 120, "rgba(255,255,255,.35)", 8, 0)).join("");


  BG.store = (o = {}) => BG.room({ wall: o.wall || "#EEF2F4", floor: o.floor || "#D9D4C7", fy: o.fy || 820 }) +
    Array.from({ length: 5 }, (_, i) => rect(120 + i * 380, 70, 220, 26, "#FFFFFF", 12, 4, "#C9D3DC")).join("");

  // ---------- motion helpers ----------
  function pop(tl, el, t, d = 0.45, from = 0) {
    tl.fromTo(el, { scale: from, opacity: 0, transformOrigin: "50% 50%" }, { scale: 1, opacity: 1, duration: d, ease: "back.out(2.2)" }, t);
  }
  function popOut(tl, el, t, d = 0.25) {
    tl.to(el, { scale: 0, opacity: 0, transformOrigin: "50% 50%", duration: d, ease: "back.in(2)" }, t);
  }
  function fadeIn(tl, el, t, d = 0.35) { tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: d, ease: "power1.out" }, t); }
  function fadeOut(tl, el, t, d = 0.3) { tl.to(el, { opacity: 0, duration: d, ease: "power1.in" }, t); }
  function slideIn(tl, el, t, dx = 0, dy = 0, d = 0.55, ease = "back.out(1.4)") {
    tl.fromTo(el, { x: dx, y: dy, opacity: 0 }, { x: 0, y: 0, opacity: 1, duration: d, ease }, t);
  }
  function slideTo(tl, el, t, x, y, d = 0.6, ease = "power2.inOut") { tl.to(el, { x, y, duration: d, ease }, t); }
  function shake(tl, el, t, d = 0.4, amp = 14) {
    const n = Math.floor(d / 0.05);
    for (let i = 0; i < n; i++) tl.to(el, { x: (i % 2 ? 1 : -1) * amp * (1 - i / n), y: (i % 3 - 1) * amp * 0.5 * (1 - i / n), duration: 0.05, ease: "none" }, t + i * 0.05);
    tl.to(el, { x: 0, y: 0, duration: 0.05 }, t + n * 0.05);
  }
  function wiggle(tl, el, t, d, amp = 8, period = 0.18, origin = "50% 50%") {
    const n = Math.floor(d / period);
    for (let i = 0; i < n; i++) tl.to(el, { rotation: i % 2 ? amp : -amp, transformOrigin: origin, duration: period, ease: "sine.inOut" }, t + i * period);
    tl.to(el, { rotation: 0, transformOrigin: origin, duration: period }, t + n * period);
  }
  function float(tl, el, t, d, amp = 12, period = 1.4) {
    const n = Math.max(1, Math.floor(d / period));
    tl.fromTo(el, { y: -amp / 2 }, { y: amp / 2, duration: period, ease: "sine.inOut", yoyo: true, repeat: n - 1 }, t);
  }
  /** draw-on for stroked paths. el selector → all paths inside get dash animation */
  function draw(tl, sel, t, d = 0.6, ease = "power1.inOut") {
    tl.fromTo(sel, { strokeDasharray: 3000, strokeDashoffset: 3000 }, { strokeDashoffset: 0, duration: d, ease }, t);
  }
  /** camera: slow push (Ken Burns) on a wrapper element */
  function push(tl, el, t, d, s0 = 1, s1 = 1.08, x0 = 0, x1 = 0, y0 = 0, y1 = 0) {
    tl.fromTo(el, { scale: s0, x: x0, y: y0, transformOrigin: "50% 50%" }, { scale: s1, x: x1, y: y1, duration: d, ease: "sine.inOut" }, t);
  }
  /** punch-in: fast zoom on a beat */
  function punch(tl, el, t, s = 1.12, d = 0.35) {
    tl.to(el, { scale: s, duration: d, ease: "power3.out", transformOrigin: "50% 50%" }, t);
  }

  /**
   * Shot list: shots = [[selector, startTime, transition?], ...]. Only one shot is visible
   * at a time. transitions: "cut" (default), "whipL", "whipR", "pop", "fade", "up".
   */
  function shots(tl, list, end) {
    window.__SHOTLOG = window.__SHOTLOG || [];
    list.forEach(([sel, t0, tr = "cut"], i) => {
      window.__SHOTLOG.push({ sel, t: +t0.toFixed(3), tr });
      const next = list[i + 1];
      const t1 = next ? next[1] : end;
      if (t0 <= 0) gsap.set(sel, { visibility: "inherit" });
      else tl.set(sel, { visibility: "inherit" }, t0);
      if (next) tl.set(sel, { visibility: "hidden" }, t1);
      if (tr === "whipL" || tr === "whipR") {
        const dx = tr === "whipL" ? 1920 : -1920;
        tl.fromTo(sel, { x: dx, filter: "blur(18px)" }, { x: 0, filter: "blur(0px)", duration: 0.32, ease: "power3.out" }, t0);
        if (i > 0) {
          const prev = list[i - 1][0];
          tl.set(prev, { visibility: "inherit" }, t0);
          tl.to(prev, { x: -dx, filter: "blur(18px)", duration: 0.32, ease: "power3.in" }, t0 - 0.0);
          tl.set(prev, { visibility: "hidden", x: 0, filter: "blur(0px)" }, t0 + 0.33);
        }
      } else if (tr === "pop") {
        tl.fromTo(sel, { scale: 0.86, opacity: 0, transformOrigin: "50% 50%" }, { scale: 1, opacity: 1, duration: 0.35, ease: "back.out(1.6)" }, t0);
      } else if (tr === "fade") {
        tl.fromTo(sel, { opacity: 0 }, { opacity: 1, duration: 0.4 }, t0);
      } else if (tr === "up") {
        tl.fromTo(sel, { y: 1080 }, { y: 0, duration: 0.45, ease: "power3.out" }, t0);
      }
    });
  }

  /** boil: flip an element's filter between seeded displacement maps at 8fps across [t0,t1] */
  function boil(tl, sel, pfx, t0, t1, fps = 8) {
    if (window.__NOBOIL) return;
    let i = 0;
    for (let t = t0; t < t1; t += 1 / fps, i++) tl.set(sel, { attr: { filter: `url(#${pfx}-boil${i % 3})` } }, t);
  }

  /** kinetic text: split an HTML element's words into spans and pop them in */
  function words(tl, el, t, stagger = 0.08, opts = {}) {
    const node = typeof el === "string" ? document.querySelector(el) : el;
    if (!node.dataset.split) {
      node.innerHTML = node.textContent.trim().split(/\s+/).map((w) => `<span class="w" style="display:inline-block">${w}</span>`).join(" ");
      node.dataset.split = "1";
    }
    const ws = node.querySelectorAll(".w");
    tl.fromTo(ws, { y: opts.y ?? 40, opacity: 0, rotation: opts.rot ?? -6, scale: 0.7 },
      { y: 0, opacity: 1, rotation: 0, scale: 1, duration: 0.42, ease: "back.out(2)", stagger }, t);
    return ws;
  }
  /** handwriting reveal left→right via clip-path */
  function write(tl, el, t, d = 0.8) {
    tl.fromTo(el, { clipPath: "inset(-20% 100% -20% -2%)" }, { clipPath: "inset(-20% -2% -20% -2%)", duration: d, ease: "power1.inOut" }, t);
  }

  // ---------- audio cue logging (collected at build time to place SFX) ----------
  window.__SFX = window.__SFX || [];
  function sfx(scene, name, t, gain = 1) { window.__SFX.push({ scene, name, t: +t.toFixed(3), gain }); }


  /**
   * scene(id): helper for building a scene's DOM.
   *   const S = R.scene("s01");
   *   S.add("a", svgInner, htmlOverlay)   → registers shot #s01-a
   *   S.mount()                            → writes all shots into the root
   * Each shot = <div class="shot"><svg><g class="art">…</g></svg>overlay</div>
   */
  function scene(id) {
    const list = [];
    return {
      id,
      add(name, svg, html = "", bg = "") {
        list.push(`<div class="shot" id="${id}-${name}">` +
          `<svg viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid slice">${bg}<g class="art" id="${id}-${name}-art">${svg}</g></svg>` +
          `${html}</div>`);
      },
      mount() {
        const root = document.getElementById(id) || document.querySelector(`[data-hf-authored-id="${id}"]`);
        root.innerHTML = `<svg width="0" height="0" style="position:absolute">${defs(id)}</svg>` +
          `<div class="cam" id="${id}-cam">${list.join("")}</div>`;
      },
    };
  }


  /**
   * cue(CUES) → q(lineId, phrase?, offset?) : scene-local time.
   * Without phrase: line start. With phrase: estimated time that phrase is spoken, by
   * weighted character position (punctuation counts as pause time).
   */
  function cue(CUES) {
    const wlen = (s) => s.replace(/[.?!]\s*/g, "@@@@@@@@").replace(/[,;:]\s*/g, "@@@@").length;
    return function q(id, phrase, off = 0) {
      const c = CUES[id];
      if (!c) throw new Error("no cue " + id);
      if (!phrase) return c[0] + off;
      if (phrase === "end") return c[1] + off;
      const i = c[2].indexOf(phrase);
      if (i < 0) throw new Error(`phrase "${phrase}" not in ${id}`);
      return c[0] + (c[1] - c[0]) * (wlen(c[2].slice(0, i)) / wlen(c[2])) + off;
    };
  }

  window.R = {
    C, FONT, FONT2, g, at, line, path, circ, ell, rect, text, rng, defs,
    person, pose, expr, blink, idle, laugh, talk, walk, flutter, P, BG,
    pop, popOut, fadeIn, fadeOut, slideIn, slideTo, shake, wiggle, float, draw, push, punch,
    shots, boil, words, write, sfx, scene, cue,
  };
})();
