/* methodology_v2 documentation viewer.
   Pure client-side, offline. Reads window.MANIFEST + window.DOCS (from docs-data.js),
   renders a grouped nav + a markdown reader with in-panel relative-link navigation,
   filter, hash routing, and a light/dark toggle. No build step, no server needed. */
(function () {
  "use strict";

  var MANIFEST = window.MANIFEST || [];
  var DOCS = window.DOCS || {};
  var GROUP_ORDER = ["(root)", "architecture", "modules", "reference", "design", "logs"];
  var GROUP_LABEL = { "(root)": "overview" };

  var sidebar = document.getElementById("sidebar");
  var docEl = document.getElementById("doc");
  var filterEl = document.getElementById("filter");
  var current = null;

  /* ---------- markdown ---------- */
  if (window.marked && window.marked.setOptions) {
    window.marked.setOptions({
      highlight: function (code, lang) {
        try {
          if (window.hljs && lang && window.hljs.getLanguage(lang)) {
            return window.hljs.highlight(code, { language: lang }).value;
          }
          if (window.hljs) return window.hljs.highlightAuto(code).value;
        } catch (e) {}
        return code;
      },
      gfm: true, breaks: false, headerIds: true, mangle: false,
    });
  }
  function md(text) {
    try { return window.marked.parse ? window.marked.parse(text) : window.marked(text); }
    catch (e) { return "<pre>" + esc(text) + "</pre>"; }
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  /* ---------- path helpers ---------- */
  function resolvePath(from, rel) {
    rel = rel.split("#")[0];
    if (!rel) return null;
    if (DOCS[rel]) return rel;                 // already a valid key
    var base = from.split("/"); base.pop();     // dir of the current doc
    rel.split("/").forEach(function (seg) {
      if (seg === "" || seg === ".") return;
      if (seg === "..") base.pop();
      else base.push(seg);
    });
    var joined = base.join("/");
    if (DOCS[joined]) return joined;
    // last-ditch: match by trailing name
    var name = rel.split("/").pop();
    var hit = MANIFEST.find(function (d) { return d.name === name; });
    return hit ? hit.path : null;
  }

  /* ---------- nav ---------- */
  function buildNav() {
    var groups = {};
    MANIFEST.forEach(function (d) { (groups[d.group] = groups[d.group] || []).push(d); });
    var keys = Object.keys(groups).sort(function (a, b) {
      var ia = GROUP_ORDER.indexOf(a), ib = GROUP_ORDER.indexOf(b);
      return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
    });
    sidebar.innerHTML = "";
    keys.forEach(function (g) {
      var gh = el("div", "nav-group", GROUP_LABEL[g] || g);
      gh.dataset.group = g;
      sidebar.appendChild(gh);
      groups[g].sort(function (a, b) { return a.name.localeCompare(b.name); }).forEach(function (d) {
        var mono = g === "modules" || g === "reference";
        var item = el("div", "nav-item" + (mono ? " mono" : ""), d.title);
        item.dataset.path = d.path;
        item.title = d.path;
        item.addEventListener("click", function () { open(d.path, true); });
        sidebar.appendChild(item);
      });
    });
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  /* ---------- open a doc ---------- */
  function open(path, pushHash) {
    var text = DOCS[path];
    if (text == null) {
      docEl.innerHTML = '<div class="reader-empty">Not found: ' + esc(path) + "</div>";
      return;
    }
    current = path;
    var entry = MANIFEST.find(function (d) { return d.path === path; }) || {};
    var crumb = (GROUP_LABEL[entry.group] || entry.group || "") + " / " + (entry.name || path);
    docEl.innerHTML = '<span class="doc-crumb">' + esc(crumb) + "</span>" + md(text);

    docEl.querySelectorAll("pre code").forEach(function (c) {
      try { window.hljs && window.hljs.highlightElement(c); } catch (e) {}
    });
    // intercept relative links -> navigate in-panel
    docEl.querySelectorAll("a[href]").forEach(function (a) {
      var href = a.getAttribute("href");
      if (/^https?:/i.test(href) || href.startsWith("mailto:")) { a.target = "_blank"; a.rel = "noopener"; return; }
      if (href.startsWith("#")) return; // in-page anchor
      a.addEventListener("click", function (ev) {
        ev.preventDefault();
        var resolved = resolvePath(current, href);
        if (resolved) open(resolved, true);
        else window.scrollTo(0, 0);
      });
    });

    sidebar.querySelectorAll(".nav-item").forEach(function (n) {
      n.classList.toggle("active", n.dataset.path === path);
    });
    var active = sidebar.querySelector(".nav-item.active");
    if (active) active.scrollIntoView({ block: "nearest" });
    document.querySelector(".reader").scrollTop = 0;
    if (pushHash) history.replaceState(null, "", "#" + path);
    document.title = (entry.title || "methodology_v2") + " — docs";
  }

  /* ---------- filter ---------- */
  function applyFilter(q) {
    q = (q || "").trim().toLowerCase();
    var visibleByGroup = {};
    sidebar.querySelectorAll(".nav-item").forEach(function (n) {
      var d = MANIFEST.find(function (x) { return x.path === n.dataset.path; }) || {};
      var hit = !q || (d.title || "").toLowerCase().indexOf(q) >= 0 || (d.path || "").toLowerCase().indexOf(q) >= 0;
      n.classList.toggle("nav-hidden", !hit);
      if (hit) visibleByGroup[d.group] = true;
    });
    sidebar.querySelectorAll(".nav-group").forEach(function (g) {
      g.classList.toggle("nav-hidden", q && !visibleByGroup[g.dataset.group]);
    });
  }

  /* ---------- theme ---------- */
  function initTheme() {
    var saved = null;
    try { saved = localStorage.getItem("mv2docs-theme"); } catch (e) {}
    if (saved) document.documentElement.setAttribute("data-theme", saved);
    syncHljsTheme();
    document.getElementById("theme-btn").addEventListener("click", function () {
      var cur = document.documentElement.getAttribute("data-theme");
      var isDark = cur === "dark" || (!cur && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
      var next = isDark ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      try { localStorage.setItem("mv2docs-theme", next); } catch (e) {}
      syncHljsTheme();
    });
  }
  function syncHljsTheme() {
    var cur = document.documentElement.getAttribute("data-theme");
    var dark = cur === "dark" || (!cur && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
    var l = document.getElementById("hljs-light"), d = document.getElementById("hljs-dark");
    if (l) l.disabled = dark;
    if (d) d.disabled = !dark;
  }

  /* ---------- boot ---------- */
  function boot() {
    if (!MANIFEST.length) {
      sidebar.innerHTML = '<div class="nav-group">no content</div>';
      docEl.innerHTML = '<div class="reader-empty">No docs loaded. Run <code>build.py</code> to generate <code>docs-data.js</code>.</div>';
      return;
    }
    buildNav();
    initTheme();
    filterEl.addEventListener("input", function () { applyFilter(filterEl.value); });

    var start = decodeURIComponent((location.hash || "").replace(/^#/, ""));
    if (start && DOCS[start]) open(start, false);
    else {
      var readme = MANIFEST.find(function (d) { return d.name === "README.md"; });
      open(readme ? readme.path : MANIFEST[0].path, false);
    }
    window.addEventListener("hashchange", function () {
      var p = decodeURIComponent((location.hash || "").replace(/^#/, ""));
      if (p && DOCS[p] && p !== current) open(p, false);
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
