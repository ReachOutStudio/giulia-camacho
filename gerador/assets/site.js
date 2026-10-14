(function () {
  "use strict";
  var $ = function (s, el) { return (el || document).querySelector(s); };

  var menuBtn = $("#menu-btn");
  if (menuBtn) {
    menuBtn.addEventListener("click", function () {
      var open = !document.body.classList.contains("menu-open");
      document.body.classList.toggle("menu-open", open);
      menuBtn.setAttribute("aria-expanded", String(open));
    });
  }

  var pv = $(".index-preview .pv");
  if (pv) {
    var links = document.querySelectorAll(".index-list a[data-src]");
    Array.prototype.forEach.call(links, function (a) {
      var show = function () {
        if (pv.getAttribute("src") === a.dataset.src) return;
        pv.removeAttribute("srcset");
        pv.width = +a.dataset.w; pv.height = +a.dataset.h;
        pv.style.background = a.dataset.avg;
        pv.srcset = a.dataset.srcset;
        pv.src = a.dataset.src;
        var cap = $("#pv-cap"); if (cap) cap.textContent = a.dataset.cap;
        Array.prototype.forEach.call(links, function (x) { x.classList.toggle("hot", x === a); });
      };
      a.addEventListener("mouseenter", show);
      a.addEventListener("focus", show);
    });
  }

  var dataEl = $("#lb-data");
  if (dataEl) {
    var data = JSON.parse(dataEl.textContent);
    var box = $("#lb"), im = $("#lb-img"), state = null;
    var pad = function (n) { return (n < 10 ? "0" : "") + n; };
    var show = function () {
      var p = data.photos[state.i];
      im.removeAttribute("src");
      im.width = p.w; im.height = p.h; im.style.background = p.avg; im.alt = p.alt;
      im.src = p.src;
      $("#lb-count").textContent = data.name + " · " + pad(state.i + 1) + " / " + pad(data.photos.length);
    };
    var open = function (i, opener) {
      state = { i: i, opener: opener };
      box.hidden = false;
      document.body.classList.add("lb-open");
      show();
      $("#lb-close").focus();
    };
    var close = function () {
      if (!state) return;
      box.hidden = true;
      document.body.classList.remove("lb-open");
      var o = state.opener; state = null;
      if (o) o.focus();
    };
    var step = function (d) {
      if (!state) return;
      var n = data.photos.length;
      state.i = (state.i + d + n) % n;
      show();
    };
    Array.prototype.forEach.call(document.querySelectorAll("button.ph[data-i]"), function (b) {
      b.addEventListener("click", function () { open(+b.dataset.i, b); });
    });
    $("#lb-close").addEventListener("click", close);
    $("#lb-prev").addEventListener("click", function () { step(-1); });
    $("#lb-next").addEventListener("click", function () { step(1); });
    box.addEventListener("click", function (ev) {
      if (ev.target === box || ev.target.classList.contains("lb-stage")) close();
    });
    document.addEventListener("keydown", function (ev) {
      if (!state) return;
      if (ev.key === "Escape") close();
      else if (ev.key === "ArrowLeft") step(-1);
      else if (ev.key === "ArrowRight") step(1);
    });
  }

  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape" && document.body.classList.contains("menu-open")) {
      document.body.classList.remove("menu-open");
      if (menuBtn) { menuBtn.setAttribute("aria-expanded", "false"); menuBtn.focus(); }
    }
  });

  var copyBtn = $("#copy-mail");
  if (copyBtn) {
    var label = copyBtn.textContent;
    copyBtn.addEventListener("click", function () {
      var done = function (ok) {
        copyBtn.textContent = ok ? copyBtn.dataset.ok : copyBtn.dataset.fail;
        setTimeout(function () { copyBtn.textContent = label; }, 2400);
      };
      var selectIt = function () {
        var r = document.createRange(); r.selectNodeContents($("#mail"));
        var sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(r);
        done(false);
      };
      try {
        navigator.clipboard.writeText(copyBtn.dataset.copy).then(function () { done(true); }, selectIt);
      } catch (err) { selectIt(); }
    });
  }

  var form = $("#form");
  if (form) {
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var st = $("#form-status");
      var name = form.elements.name.value.trim(), email = form.elements.email.value.trim(), msg = form.elements.msg.value.trim();
      if (!name || !email || !msg) { st.textContent = form.dataset.required; st.className = "warn"; return; }
      var lines = [msg, "", "—", name, email, form.elements.type.value];
      if (form.elements.date.value) lines.push(form.elements.date.value);
      var href = "mailto:" + form.dataset.to + "?subject=" + encodeURIComponent(form.dataset.subject + " · " + name) + "&body=" + encodeURIComponent(lines.join("\n"));
      window.location.href = href;
      st.textContent = form.dataset.sent; st.className = "ok";
    });
  }
})();
