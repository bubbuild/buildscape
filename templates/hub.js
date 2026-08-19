(function() {
  var catCounts = {{ cat_counts_json | safe }};
  var totalItems = {{ total_items }};

  var searchInput = document.getElementById("search");
  var tabs = document.querySelectorAll(".tab");
  var sections = document.querySelectorAll(".category-section");
  var cards = document.querySelectorAll(".card");
  var shownCount = document.getElementById("shown-count");
  var emptyState = document.getElementById("empty-state");
  var themeToggle = document.querySelector("[data-theme-toggle]");
  var themeColor = document.getElementById("theme-color");
  var mobileMenu = document.querySelector(".mobile-menu");

  var activeCat = "all";

  function showLogoFallback(image) {
    var slot = image.closest(".card-logo-slot");
    if (!slot) return;
    image.hidden = true;
    slot.classList.add("is-fallback");
  }

  function classifyLogoVisibility(image) {
    var slot = image.closest(".card-logo-slot");
    if (!slot || !image.naturalWidth || !image.naturalHeight) return;

    try {
      var canvas = document.createElement("canvas");
      canvas.width = 32;
      canvas.height = 32;
      var context = canvas.getContext("2d", { willReadFrequently: true });
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      var pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
      var visibleWeight = 0;
      var lightWeight = 0;
      var darkWeight = 0;

      for (var index = 0; index < pixels.length; index += 4) {
        var alpha = pixels[index + 3];
        if (alpha < 16) continue;
        visibleWeight += alpha;
        if (pixels[index] >= 238 && pixels[index + 1] >= 238 && pixels[index + 2] >= 238) {
          lightWeight += alpha;
        }
        if (pixels[index] <= 35 && pixels[index + 1] <= 35 && pixels[index + 2] <= 35) {
          darkWeight += alpha;
        }
      }

      if (!visibleWeight) {
        showLogoFallback(image);
        return;
      }
      slot.classList.toggle("is-light-invisible", lightWeight / visibleWeight >= .92);
      slot.classList.toggle("is-dark-invisible", darkWeight / visibleWeight >= .92);
    } catch (error) {
      // Keep the original logo if the browser cannot inspect its pixels.
    }
  }

  document.querySelectorAll(".card-logo").forEach(function(image) {
    image.addEventListener("error", function() {
      showLogoFallback(image);
    });
    image.addEventListener("load", function() {
      classifyLogoVisibility(image);
    });

    if (image.complete && image.naturalWidth === 0) {
      showLogoFallback(image);
    } else if (image.complete) {
      classifyLogoVisibility(image);
    }
  });

  tabs.forEach(function(tab) {
    var cat = tab.dataset.cat;
    var count = cat === "all" ? totalItems : (catCounts[cat] || 0);
    var span = document.createElement("span");
    span.className = "count";
    span.textContent = count;
    tab.appendChild(span);
    tab.setAttribute("aria-label", (cat === "all" ? "All" : cat) + ", " + count + (count === 1 ? " item" : " items"));
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
      tabs.forEach(function(t) {
        t.classList.remove("active");
        t.setAttribute("aria-pressed", "false");
      });
      tab.classList.add("active");
      tab.setAttribute("aria-pressed", "true");
      activeCat = tab.dataset.cat;
      applyFilters();
    });
  });

  searchInput.addEventListener("input", applyFilters);

  document.addEventListener("keydown", function(event) {
    var target = event.target;
    var isTyping = target instanceof HTMLInputElement
      || target instanceof HTMLTextAreaElement
      || target.isContentEditable;

    if (event.key === "/" && !isTyping && !event.ctrlKey && !event.metaKey && !event.altKey) {
      event.preventDefault();
      searchInput.focus();
    }

    if (event.key === "Escape" && document.activeElement === searchInput && searchInput.value) {
      searchInput.value = "";
      applyFilters();
    }
  });

  function updateThemeToggle(theme) {
    var dark = theme === "dark";
    themeToggle.setAttribute("aria-pressed", dark ? "true" : "false");
    themeToggle.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
    themeToggle.title = dark ? "Switch to light mode" : "Switch to dark mode";
    themeColor.content = dark ? "#252525" : "#ffffff";
  }

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    updateThemeToggle(theme);
  }

  if (themeToggle) {
    updateThemeToggle(document.documentElement.dataset.theme || "light");
    themeToggle.addEventListener("click", function() {
      var nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
      var switchTheme = function() { applyTheme(nextTheme); };

      try {
        localStorage.setItem("starlight-theme", nextTheme);
      } catch (error) {
        // The theme still applies for this visit when storage is unavailable.
      }

      if (document.startViewTransition && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        try {
          var transition = document.startViewTransition(switchTheme);
          transition.finished.catch(function() {
            // Navigation or another transition can intentionally abort this animation.
          });
        } catch (error) {
          switchTheme();
        }
      } else {
        switchTheme();
      }
    });
  }

  if (mobileMenu) {
    var mobileMenuSummary = mobileMenu.querySelector("summary");
    mobileMenu.addEventListener("toggle", function() {
      mobileMenuSummary.setAttribute("aria-label", mobileMenu.open ? "Close navigation menu" : "Open navigation menu");
    });
    mobileMenu.addEventListener("keydown", function(event) {
      if (event.key === "Escape" && mobileMenu.open) {
        mobileMenu.open = false;
        mobileMenuSummary.focus();
      }
    });
    document.addEventListener("click", function(event) {
      if (mobileMenu.open && !mobileMenu.contains(event.target)) {
        mobileMenu.open = false;
      }
    });
  }

  document.addEventListener("click", function(e) {
    var btn = e.target.closest(".copy-btn");
    if (!btn) return;
    var cmd = btn.dataset.cmd;
    navigator.clipboard.writeText(cmd).then(function() {
      btn.classList.add("copied");
      var orig = btn.innerHTML;
      var origLabel = btn.getAttribute("aria-label");
      btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        + 'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        + '<polyline points="20 6 9 17 4 12"/></svg>';
      btn.setAttribute("aria-label", "Install command copied");
      btn.title = "Copied";
      setTimeout(function() {
        btn.classList.remove("copied");
        btn.innerHTML = orig;
        btn.setAttribute("aria-label", origLabel);
        btn.title = "Copy install command";
      }, 1500);
    });
  });

  applyFilters();
})();
