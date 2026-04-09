(function() {
  var catCounts = {{ cat_counts_json | safe }};
  var totalItems = {{ total_items }};

  var searchInput = document.getElementById("search");
  var tabs = document.querySelectorAll(".tab");
  var sections = document.querySelectorAll(".category-section");
  var cards = document.querySelectorAll(".card");
  var shownCount = document.getElementById("shown-count");
  var emptyState = document.getElementById("empty-state");

  var activeCat = "all";

  tabs.forEach(function(tab) {
    var cat = tab.dataset.cat;
    var count = cat === "all" ? totalItems : (catCounts[cat] || 0);
    var span = document.createElement("span");
    span.className = "count";
    span.textContent = count;
    tab.appendChild(span);
  });

  function applyFilters() {
    var query = searchInput.value.trim().toLowerCase();
    var shown = 0;

    sections.forEach(function(sec) {
      var secCat = sec.dataset.category;
      var catMatch = activeCat === "all" || secCat === activeCat;
      if (!catMatch) {
        sec.classList.remove("visible");
        return;
      }
      sec.classList.add("visible");
    });

    cards.forEach(function(card) {
      var cardSection = card.closest(".category-section");
      if (!cardSection || !cardSection.classList.contains("visible")) {
        card.classList.add("hidden");
        return;
      }
      var searchText = card.dataset.search || "";
      if (query && searchText.indexOf(query) === -1) {
        card.classList.add("hidden");
      } else {
        card.classList.remove("hidden");
        shown++;
      }
    });

    document.querySelectorAll(".subcategory-group").forEach(function(group) {
      var visibleCards = group.querySelectorAll(".card:not(.hidden)");
      group.style.display = visibleCards.length ? "" : "none";
    });

    shownCount.textContent = shown;
    emptyState.classList.toggle("visible", shown === 0);
  }

  tabs.forEach(function(tab) {
    tab.addEventListener("click", function() {
      tabs.forEach(function(t) { t.classList.remove("active"); });
      tab.classList.add("active");
      activeCat = tab.dataset.cat;
      applyFilters();
    });
  });

  searchInput.addEventListener("input", applyFilters);

  document.addEventListener("click", function(e) {
    var btn = e.target.closest(".copy-btn");
    if (!btn) return;
    var cmd = btn.dataset.cmd;
    navigator.clipboard.writeText(cmd).then(function() {
      btn.classList.add("copied");
      var orig = btn.innerHTML;
      btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        + 'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        + '<polyline points="20 6 9 17 4 12"/></svg>';
      setTimeout(function() {
        btn.classList.remove("copied");
        btn.innerHTML = orig;
      }, 1500);
    });
  });

  applyFilters();
})();
