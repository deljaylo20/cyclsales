/*
  SITE SETTINGS — fill these in before launch.
    formEndpoint        URL that receives the Contact form (e.g. a GoHighLevel / Formspree / Pages Function endpoint). POSTs JSON.
    newsletterEndpoint  URL that receives newsletter sign-ups. POSTs JSON.
    email               Susan's public email. Used as a mailto fallback if an endpoint is blank.
*/
window.SITE = {
  formEndpoint: "",
  newsletterEndpoint: "",
  email: ""
};

(function () {
  const works = window.ARTWORKS || [];
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  // Generated color-field placeholder, used until a real image is added.
  function placeholder(w) {
    const [a, b, c] = w.hue || [30, 20, 200];
    return `<div class="ph" aria-hidden="true" style="background:
      radial-gradient(120% 70% at 30% 20%, hsl(${a} 38% 72% / .95), transparent 60%),
      radial-gradient(90% 80% at 80% 90%, hsl(${b} 30% 38% / .9), transparent 65%),
      linear-gradient(160deg, hsl(${c} 18% 86%), hsl(${b} 22% 58%))"></div>`;
  }
  function artHTML(w, opts = {}) {
    const alt = esc(w.title + (w.medium ? ", " + w.medium : ""));
    const inner = w.src ? `<img src="${esc(w.src)}" alt="${alt}" loading="${opts.eager ? "eager" : "lazy"}">` : placeholder(w);
    const style = opts.ratio ? ` style="aspect-ratio:${w.ratio || 1}"` : "";
    return `<div class="art"${style}${w.src ? "" : ` role="img" aria-label="${alt} (placeholder)"`}>${inner}</div>`;
  }
  const detail = (w) => [w.year, w.medium, w.size].filter(Boolean).join(" · ");

  const no = (i) => String(i + 1).padStart(2, "0");
  function tile(w, i, opts) {
    const right = [w.medium, w.year, w.status].filter(Boolean).join(" · ");
    return `<button class="item" type="button" data-i="${i}" aria-label="View ${esc(w.title)}">
      ${artHTML(w, opts)}
      <div class="meta"><span class="n">${no(i)}</span><span class="t">${esc(w.title)}</span><span class="r">${esc(right)}</span></div>
    </button>`;
  }

  // ---------- Lightbox ----------
  let list = [], pos = 0, lastFocus = null;
  const lb = document.createElement("div");
  lb.className = "lightbox";
  lb.setAttribute("role", "dialog");
  lb.setAttribute("aria-modal", "true");
  lb.setAttribute("aria-label", "Artwork viewer");
  lb.innerHTML = `<div class="lb-stage"></div><div class="lb-caption" aria-live="polite"></div>
    <button class="lb-btn lb-close" aria-label="Close">&times;</button>
    <button class="lb-btn lb-prev" aria-label="Previous">&#8592;</button>
    <button class="lb-btn lb-next" aria-label="Next">&#8594;</button>`;
  document.body.appendChild(lb);
  const stage = lb.querySelector(".lb-stage"), cap = lb.querySelector(".lb-caption");

  function show() {
    const w = works[list[pos]];
    if (w.src) stage.innerHTML = `<img src="${esc(w.src)}" alt="${esc(w.title)}">`;
    else stage.innerHTML = `<div class="art" style="aspect-ratio:${w.ratio || 1};height:100%;max-height:100%">${placeholder(w)}</div>`;
    const d = detail(w);
    cap.innerHTML = `<span class="n">No. ${no(list[pos])}</span><span class="t">${esc(w.title)}</span>${esc(d)}${d && w.status ? " · " : ""}${esc(w.status || "")}
      <a class="link" href="contact.html?piece=${encodeURIComponent(w.title)}">Inquire</a>`;
    const multi = list.length > 1;
    lb.querySelector(".lb-prev").hidden = lb.querySelector(".lb-next").hidden = !multi;
  }
  function open(indices, i) {
    list = indices; pos = Math.max(0, indices.indexOf(i));
    lastFocus = document.activeElement;
    show(); lb.classList.add("open"); document.body.style.overflow = "hidden";
    lb.querySelector(".lb-close").focus();
  }
  function close() { lb.classList.remove("open"); document.body.style.overflow = ""; lastFocus && lastFocus.focus(); }
  const step = (d) => { pos = (pos + d + list.length) % list.length; show(); };
  lb.querySelector(".lb-close").onclick = close;
  lb.querySelector(".lb-prev").onclick = () => step(-1);
  lb.querySelector(".lb-next").onclick = () => step(1);
  lb.addEventListener("click", (e) => { if (e.target === lb || e.target === stage) close(); });
  document.addEventListener("keydown", (e) => {
    if (!lb.classList.contains("open")) return;
    if (e.key === "Escape") close();
    if (e.key === "ArrowLeft") step(-1);
    if (e.key === "ArrowRight") step(1);
    if (e.key === "Tab") { // keep focus inside the viewer
      const f = [...lb.querySelectorAll("button:not([hidden]), a")];
      const first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
  let tx = null;
  lb.addEventListener("touchstart", (e) => { tx = e.touches[0].clientX; }, { passive: true });
  lb.addEventListener("touchend", (e) => { if (tx === null) return; const dx = e.changedTouches[0].clientX - tx; if (Math.abs(dx) > 50) step(dx < 0 ? 1 : -1); tx = null; });

  function bind(container, indices) {
    container.addEventListener("click", (e) => {
      const b = e.target.closest(".item"); if (b) open(indices, +b.dataset.i);
    });
  }

  // ---------- Home page ----------
  const slidesEl = document.getElementById("hero-slides");
  const featured = works.map((w, i) => (w.featured ? i : -1)).filter((i) => i >= 0);
  if (slidesEl && featured.length) {
    const capEl = document.getElementById("hero-caption"), dotsEl = document.getElementById("hero-dots"), pauseEl = document.getElementById("hero-pause");
    slidesEl.innerHTML = featured.map((i, n) => {
      const w = works[i];
      const img = w.src ? `<img src="${esc(w.src)}" alt="${esc(w.title)}" style="object-position:${esc(w.focus || "center")}" ${n ? 'loading="lazy"' : 'fetchpriority="high"'}>` : placeholder(w);
      return `<button type="button" class="slide${n ? "" : " on"}" data-i="${i}" aria-label="View ${esc(w.title)}" ${n ? 'tabindex="-1"' : ""}>${img}</button>`;
    }).join("");
    dotsEl.innerHTML = featured.map((_, n) => `<button type="button" aria-label="Show painting ${n + 1}"${n ? "" : ' aria-current="true"'}></button>`).join("");
    const slides = [...slidesEl.children], dots = [...dotsEl.children];
    let cur = 0, timer = null;
    const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    let playing = !reduce && featured.length > 1;
    function go(n) {
      slides[cur].classList.remove("on"); slides[cur].tabIndex = -1; dots[cur].removeAttribute("aria-current");
      cur = (n + slides.length) % slides.length;
      slides[cur].classList.add("on"); slides[cur].tabIndex = 0; dots[cur].setAttribute("aria-current", "true");
      const w = works[featured[cur]];
      capEl.innerHTML = `<em>${esc(w.title)}</em>${detail(w) ? " &middot; " + esc(detail(w)) : ""}`;
    }
    function tick() { clearInterval(timer); if (playing) timer = setInterval(() => go(cur + 1), 6000); }
    function setPlaying(p) { playing = p; pauseEl.textContent = p ? "Pause" : "Play"; pauseEl.setAttribute("aria-label", p ? "Pause slideshow" : "Play slideshow"); tick(); }
    slidesEl.addEventListener("click", (e) => { const s = e.target.closest(".slide"); if (s) open(featured, +s.dataset.i); });
    dotsEl.addEventListener("click", (e) => { const d = dots.indexOf(e.target); if (d >= 0) { go(d); tick(); } });
    pauseEl.addEventListener("click", () => setPlaying(!playing));
    if (featured.length < 2) { dotsEl.hidden = pauseEl.hidden = true; }
    go(0); setPlaying(playing);
  }
  const selEl = document.getElementById("selected");
  if (selEl) {
    const picks = featured.slice(0, featured.length >= 6 ? 6 : 4);
    selEl.innerHTML = picks.map((i) => tile(works[i], i, { ratio: true })).join("");
    bind(selEl, picks);
  }

  // ---------- Gallery page ----------
  const galEl = document.getElementById("gallery");
  if (galEl) {
    const filEl = document.getElementById("filters");
    const cats = [...new Set(works.map((w) => w.category).filter(Boolean))];
    let current = "All";
    function render() {
      const idx = works.map((w, i) => i).filter((i) => current === "All" || works[i].category === current);
      galEl.innerHTML = idx.map((i) => tile(works[i], i, { ratio: true })).join("");
      galEl._indices = idx;
    }
    galEl.addEventListener("click", (e) => { const b = e.target.closest(".item"); if (b) open(galEl._indices, +b.dataset.i); });
    if (filEl && cats.length > 1) {
      filEl.innerHTML = ["All", ...cats].map((c) => `<button type="button" aria-pressed="${c === "All"}">${esc(c)}</button>`).join("");
      filEl.addEventListener("click", (e) => {
        const b = e.target.closest("button"); if (!b) return;
        current = b.textContent;
        filEl.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", x === b));
        render();
      });
    }
    render();
  }

  // ---------- Forms ----------
  async function submit(form, endpoint, subject) {
    const status = form.querySelector(".form-status");
    const data = Object.fromEntries(new FormData(form).entries());
    if (data.website) return; // honeypot
    const say = (m) => { if (status) status.textContent = m; };
    if (endpoint) {
      say("Sending…");
      try {
        const r = await fetch(endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
        if (!r.ok) throw new Error(r.status);
        form.reset(); say(form.dataset.success || "Thank you — your message is on its way.");
      } catch (err) { say("Something went wrong. Please try again, or email directly."); }
    } else if (window.SITE.email) {
      const body = Object.entries(data).filter(([k]) => k !== "website").map(([k, v]) => `${k}: ${v}`).join("\n");
      location.href = `mailto:${window.SITE.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    } else {
      say("This form isn't connected yet. (Site owner: set formEndpoint / newsletterEndpoint / email in assets/site.js.)");
    }
  }
  document.querySelectorAll("form[data-form]").forEach((f) => {
    f.addEventListener("submit", (e) => {
      e.preventDefault();
      const kind = f.dataset.form;
      submit(f, kind === "newsletter" ? window.SITE.newsletterEndpoint : window.SITE.formEndpoint, kind === "newsletter" ? "Newsletter sign-up" : "Website inquiry");
    });
  });

  // Pre-fill the contact form when arriving from "Inquire" on a piece.
  const piece = new URLSearchParams(location.search).get("piece");
  const msg = document.getElementById("message"), type = document.getElementById("inquiry");
  if (piece && msg) {
    msg.value = `I'm interested in "${piece}". `;
    if (type) type.value = "Purchasing a piece";
  }

  // Statement that fills in word by word as it scrolls into view.
  document.querySelectorAll("[data-reveal]").forEach((el) => {
    const text = el.textContent.trim(), words = text.split(/\s+/);
    el.innerHTML = `<span class="sr-only">${esc(text)}</span>` + words.map((w) => `<span class="w" aria-hidden="true">${esc(w)} </span>`).join("");
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) { el.classList.add("done"); return; }
    const spans = [...el.querySelectorAll(".w")];
    let ticking = false;
    function update() {
      ticking = false;
      const r = el.getBoundingClientRect(), vh = innerHeight;
      // 0 when the text top is 90% down the screen, fully lit by the time it reaches 40%
      const p = Math.min(1, Math.max(0, (vh * 0.9 - r.top) / (vh * 0.5)));
      const lit = Math.round(p * spans.length);
      spans.forEach((s, k) => s.classList.toggle("on", k < lit));
    }
    addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
    addEventListener("resize", update);
    update();
  });

  // Studio local time in the footer.
  const clock = document.getElementById("local-time");
  if (clock) {
    const fmt = new Intl.DateTimeFormat("en-US", { timeZone: "America/Chicago", hour: "numeric", minute: "2-digit" });
    const set = () => { const d = new Date(); clock.textContent = fmt.format(d); clock.dateTime = d.toISOString(); };
    set(); setInterval(set, 30000);
  }

  const yr = document.getElementById("year");
  if (yr) yr.textContent = new Date().getFullYear();
})();
