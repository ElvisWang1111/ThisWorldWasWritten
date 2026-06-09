// Title search using the generated SEARCH_INDEX (see search_index.js).
(function () {
  var box = document.getElementById("searchbox");
  var list = document.getElementById("suggestions");
  if (!box || !list || typeof SEARCH_INDEX === "undefined") return;

  var REL = (window.SITE_REL || "");
  var active = -1;

  function clear() {
    list.innerHTML = "";
    list.style.display = "none";
    active = -1;
  }

  function render(matches) {
    if (!matches.length) { clear(); return; }
    list.innerHTML = matches
      .map(function (m) {
        return '<li data-href="' + REL + "wiki/" + m.slug + '.html">' +
               m.title + "</li>";
      })
      .join("");
    list.style.display = "block";
    Array.prototype.forEach.call(list.children, function (li) {
      li.addEventListener("mousedown", function () {
        window.location.href = li.getAttribute("data-href");
      });
    });
  }

  box.addEventListener("input", function () {
    var q = box.value.trim().toLowerCase();
    if (!q) { clear(); return; }
    var matches = SEARCH_INDEX.filter(function (p) {
      return p.title.toLowerCase().indexOf(q) !== -1;
    }).slice(0, 10);
    render(matches);
  });

  box.addEventListener("keydown", function (e) {
    var items = list.children;
    if (e.key === "ArrowDown") {
      active = Math.min(active + 1, items.length - 1);
    } else if (e.key === "ArrowUp") {
      active = Math.max(active - 1, 0);
    } else if (e.key === "Enter") {
      if (active >= 0 && items[active]) {
        window.location.href = items[active].getAttribute("data-href");
        e.preventDefault();
      }
      return;
    } else {
      return;
    }
    Array.prototype.forEach.call(items, function (li, i) {
      li.className = i === active ? "active" : "";
    });
    e.preventDefault();
  });

  document.addEventListener("click", function (e) {
    if (!list.contains(e.target) && e.target !== box) clear();
  });
})();

function doSearch(e) {
  e.preventDefault();
  var first = document.querySelector("#suggestions li");
  if (first) window.location.href = first.getAttribute("data-href");
  return false;
}
