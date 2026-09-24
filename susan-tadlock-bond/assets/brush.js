/*
  Paintbrush cursor + watercolor trail.
  The trail is drawn on a canvas that sits BEHIND the page content, so paint only shows
  on the white background and never covers artwork or text. Strokes fade in about a second.
  Off on touch devices and when the visitor prefers reduced motion.
*/
(function () {
  const fine = matchMedia("(hover: hover) and (pointer: fine)").matches;
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!fine) return;

  // ---------- Cursor ----------
  const brush = (tip) => `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
    <g transform="rotate(45 16 16)">
      <rect x="14" y="-3" width="4" height="17" rx="2" fill="#2a2522"/>
      <rect x="13.4" y="13" width="5.2" height="6" rx="1" fill="#b9b9b9" stroke="#6d6d6d" stroke-width=".6"/>
      <path d="M13.4 19 C13 23 14.6 27.5 16 30 C17.4 27.5 19 23 18.6 19 Z" fill="${tip}" stroke="#2a2522" stroke-width=".6"/>
    </g></svg>`;
  const url = (svg) => `url("data:image/svg+xml,${encodeURIComponent(svg.replace(/\s+/g, " "))}") 5 27`;
  const style = document.createElement("style");
  style.textContent = `
    html, body { cursor: ${url(brush("#d8c7a8"))}, auto; }
    a, button, [role="button"], label, select, summary, .item, .slide, .hero-art { cursor: ${url(brush("#2b3a9a"))}, pointer !important; }
    input, textarea { cursor: text; }
    #paint-trail { position: fixed; inset: 0; width: 100vw; height: 100vh; z-index: -1; pointer-events: none; }
  `;
  document.head.appendChild(style);
  if (reduce) return;

  // ---------- Watercolor trail ----------
  const cv = document.createElement("canvas");
  cv.id = "paint-trail";
  cv.setAttribute("aria-hidden", "true");
  document.body.prepend(cv);
  const ctx = cv.getContext("2d");
  let dpr = 1;
  function size() {
    dpr = Math.min(2, window.devicePixelRatio || 1);
    cv.width = innerWidth * dpr; cv.height = innerHeight * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.lineCap = "round"; ctx.lineJoin = "round";
  }
  size(); addEventListener("resize", size);

  // Pigments pulled from Susan's paintings: ultramarine, cerulean, violet, rose, sap green, cadmium orange.
  const pigments = [[228, 56, 38], [210, 52, 50], [256, 38, 55], [340, 44, 60], [92, 32, 50], [28, 70, 54]];
  let hue = 0, last = null, active = false, raf = 0, idle = 0;

  function mix(t) { // blend smoothly between neighbouring pigments
    const n = pigments.length, i = Math.floor(t) % n, f = t - Math.floor(t);
    const a = pigments[i], b = pigments[(i + 1) % n];
    const h = a[0] + (((b[0] - a[0] + 540) % 360) - 180) * f;
    return [h, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f];
  }

  addEventListener("pointermove", (e) => {
    if (e.pointerType !== "mouse") return;
    const p = { x: e.clientX, y: e.clientY };
    if (last) {
      const dx = p.x - last.x, dy = p.y - last.y, d = Math.hypot(dx, dy);
      if (d > 0.5 && d < 400) {
        hue += d / 900;
        const [h, s, l] = mix(hue);
        const w = Math.max(3, 16 - d * 0.18);          // faster = thinner, like a real brush
        // wide pale wash, then a denser core — reads as watercolor rather than a line
        ctx.strokeStyle = `hsla(${h}, ${s}%, ${l}%, .14)`; ctx.lineWidth = w * 2.2;
        ctx.beginPath(); ctx.moveTo(last.x, last.y); ctx.lineTo(p.x, p.y); ctx.stroke();
        ctx.strokeStyle = `hsla(${h}, ${s}%, ${l}%, .30)`; ctx.lineWidth = w;
        ctx.beginPath(); ctx.moveTo(last.x, last.y); ctx.lineTo(p.x, p.y); ctx.stroke();
        if (Math.random() < 0.08) {                      // an occasional pigment bloom
          ctx.fillStyle = `hsla(${h}, ${s}%, ${l}%, .08)`;
          ctx.beginPath(); ctx.arc(p.x + (Math.random() - .5) * w, p.y + (Math.random() - .5) * w, w * (1 + Math.random()), 0, 7); ctx.fill();
        }
      }
    }
    last = p; idle = 0;
    if (!active) { active = true; raf = requestAnimationFrame(fade); }
  }, { passive: true });
  document.addEventListener("mouseleave", () => { last = null; });
  addEventListener("scroll", () => { last = null; }, { passive: true }); // don't draw a line across a scroll jump

  function fade() {
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalCompositeOperation = "destination-out";
    ctx.fillStyle = "rgba(0,0,0,.035)";
    ctx.fillRect(0, 0, cv.width, cv.height);
    ctx.restore();
    // stop the loop once the paper is clean (~2s after the mouse stops)
    if (++idle > 160) { ctx.clearRect(0, 0, cv.width, cv.height); active = false; return; }
    raf = requestAnimationFrame(fade);
  }
})();
