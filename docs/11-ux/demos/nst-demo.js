/* Local-only demo chrome helpers. Keys 1–6 switch workspaces; 7–9 overlay / incident / 8-vendor lab. */
(function () {
  var pages = {
    "1": "01-inventory.html",
    "2": "02-maps-hub.html",
    "3": "03-find.html",
    "4": "04-change.html",
    "5": "05-evidence.html",
    "6": "06-settings-vault.html",
    "7": "07-maps-utilization.html",
    "8": "08-e2e-incident.html",
    "9": "09-offline-8vendor-lab.html"
  };

  document.addEventListener("keydown", function (e) {
    var t = e.target;
    if (!t) return;
    var tag = (t.tagName || "").toUpperCase();
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || t.isContentEditable) return;
    if (pages[e.key]) {
      window.location.href = pages[e.key];
    }
  });

  window.nstDemoSetTask = function (mode) {
    var el = document.getElementById("task-strip-body");
    var cancel = document.getElementById("btn-cancel");
    if (!el) return;
    if (mode === "running") {
      el.innerHTML =
        "<strong>Standard L2 map</strong> · CORE-01 done · <span>4/12</span> · 00:41";
      el.className = "";
      if (cancel) cancel.disabled = false;
    } else if (mode === "cancelled") {
      el.innerHTML =
        "<strong>Standard L2 map</strong> · cancelled — <span>partial — not complete truth</span>";
      el.className = "";
      if (cancel) cancel.disabled = true;
    } else {
      el.innerHTML = '<span class="idle">No running job</span>';
      el.className = "";
      if (cancel) cancel.disabled = true;
    }
  };

  var toggle = document.getElementById("btn-inspector");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var app = document.querySelector(".app");
      var closed = app.classList.toggle("insp-closed");
      toggle.setAttribute("aria-expanded", closed ? "false" : "true");
      toggle.textContent = closed ? "Show inspector" : "Hide inspector";
    });
  }
})();
