// Custom JavaScript for HRNGGUI Documentation

document.addEventListener("DOMContentLoaded", function () {
  // Initialize features
  initializeCollapsibles();
  initializeCopyButtons();
  initializeTooltips();
  initializeAPIHighlighting();
  initializeSearchEnhancements();
  initializePrintOptimization();

  console.log("HRNGGUI Documentation initialized");
});

// Collapsible sections functionality
function initializeCollapsibles() {
  const collapsibles = document.querySelectorAll(".collapsible-header");

  collapsibles.forEach((header) => {
    header.addEventListener("click", function () {
      const parent = this.parentElement;
      const content = parent.querySelector(".collapsible-content");

      parent.classList.toggle("active");

      if (parent.classList.contains("active")) {
        content.style.display = "block";
        this.innerHTML = this.innerHTML.replace("▶", "▼");
      } else {
        content.style.display = "none";
        this.innerHTML = this.innerHTML.replace("▼", "▶");
      }
    });
  });
}

// Copy button for code blocks
function initializeCopyButtons() {
  const codeBlocks = document.querySelectorAll("pre code");

  codeBlocks.forEach((block) => {
    const wrapper = document.createElement("div");
    wrapper.className = "code-wrapper";
    wrapper.style.position = "relative";

    const copyButton = document.createElement("button");
    copyButton.className = "copy-button";
    copyButton.innerHTML = "📋";
    copyButton.title = "Code kopieren";
    copyButton.style.cssText = `
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            background: var(--primary-color);
            color: white;
            border: none;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8rem;
            opacity: 0.8;
            transition: opacity 0.2s ease;
        `;

    copyButton.addEventListener("mouseenter", () => {
      copyButton.style.opacity = "1";
    });

    copyButton.addEventListener("mouseleave", () => {
      copyButton.style.opacity = "0.8";
    });

    copyButton.addEventListener("click", function () {
      const code = block.textContent;
      navigator.clipboard
        .writeText(code)
        .then(() => {
          copyButton.innerHTML = "✓";
          copyButton.style.background = "var(--success-color)";

          setTimeout(() => {
            copyButton.innerHTML = "📋";
            copyButton.style.background = "var(--primary-color)";
          }, 2000);
        })
        .catch((err) => {
          console.error("Fehler beim Kopieren:", err);
          copyButton.innerHTML = "✗";
          copyButton.style.background = "var(--error-color)";

          setTimeout(() => {
            copyButton.innerHTML = "📋";
            copyButton.style.background = "var(--primary-color)";
          }, 2000);
        });
    });

    // Wrapper um den Code-Block erstellen
    block.parentNode.insertBefore(wrapper, block);
    wrapper.appendChild(block);
    wrapper.appendChild(copyButton);
  });
}

// Tooltip functionality
function initializeTooltips() {
  const tooltips = document.querySelectorAll(".tooltip");

  tooltips.forEach((tooltip) => {
    const tooltipText = tooltip.getAttribute("data-tooltip");
    if (!tooltipText) return;

    const tooltipElement = document.createElement("div");
    tooltipElement.className = "tooltip-content";
    tooltipElement.textContent = tooltipText;
    tooltipElement.style.cssText = `
            position: absolute;
            background: var(--text-color);
            color: var(--bg-color);
            padding: 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            white-space: nowrap;
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.2s ease, visibility 0.2s ease;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            margin-bottom: 0.5rem;
        `;

    tooltip.appendChild(tooltipElement);

    tooltip.addEventListener("mouseenter", () => {
      tooltipElement.style.opacity = "1";
      tooltipElement.style.visibility = "visible";
    });

    tooltip.addEventListener("mouseleave", () => {
      tooltipElement.style.opacity = "0";
      tooltipElement.style.visibility = "hidden";
    });
  });
}

// API documentation highlighting
function initializeAPIHighlighting() {
  // Highlight method signatures
  const methodSignatures = document.querySelectorAll("code");

  methodSignatures.forEach((code) => {
    const text = code.textContent;

    // Python method pattern
    if (text.match(/^def \w+\(/)) {
      code.classList.add("api-method-signature");
      code.style.cssText = `
                background-color: var(--code-bg);
                border-left: 3px solid var(--primary-color);
                padding: 0.5rem;
                display: block;
                margin: 0.5rem 0;
                border-radius: 0 4px 4px 0;
            `;
    }

    // Class pattern
    if (text.match(/^class \w+/)) {
      code.classList.add("api-class-signature");
      code.style.cssText = `
                background-color: var(--code-bg);
                border-left: 3px solid var(--success-color);
                padding: 0.5rem;
                display: block;
                margin: 0.5rem 0;
                border-radius: 0 4px 4px 0;
                font-weight: 600;
            `;
    }
  });
}

// Search enhancements
function initializeSearchEnhancements() {
  const searchInput = document.querySelector(".search-input");
  if (!searchInput) return;

  // Add search suggestions
  const suggestions = [
    "DataController",
    "MainWindow",
    "Arduino",
    "GMCounter",
    "PlotWidget",
    "add_data_point",
    "get_statistics",
    "send_command",
    "installation",
    "configuration",
    "troubleshooting",
  ];

  const suggestionContainer = document.createElement("div");
  suggestionContainer.className = "search-suggestions";
  suggestionContainer.style.cssText = `
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: var(--bg-color);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        max-height: 200px;
        overflow-y: auto;
        z-index: 1000;
        display: none;
    `;

  searchInput.parentNode.style.position = "relative";
  searchInput.parentNode.appendChild(suggestionContainer);

  searchInput.addEventListener("input", function () {
    const query = this.value.toLowerCase();

    if (query.length < 2) {
      suggestionContainer.style.display = "none";
      return;
    }

    const matches = suggestions.filter((suggestion) =>
      suggestion.toLowerCase().includes(query)
    );

    if (matches.length > 0) {
      suggestionContainer.innerHTML = matches
        .map(
          (match) =>
            `<div class="search-suggestion" style="padding: 0.5rem; cursor: pointer; border-bottom: 1px solid var(--border-color);">${match}</div>`
        )
        .join("");

      suggestionContainer.style.display = "block";

      // Add click handlers
      suggestionContainer
        .querySelectorAll(".search-suggestion")
        .forEach((item) => {
          item.addEventListener("click", function () {
            searchInput.value = this.textContent;
            suggestionContainer.style.display = "none";
            // Trigger search
            searchInput.dispatchEvent(new Event("input"));
          });
        });
    } else {
      suggestionContainer.style.display = "none";
    }
  });

  // Hide suggestions when clicking outside
  document.addEventListener("click", function (e) {
    if (
      !searchInput.contains(e.target) &&
      !suggestionContainer.contains(e.target)
    ) {
      suggestionContainer.style.display = "none";
    }
  });
}

// Print optimization
function initializePrintOptimization() {
  // Add print button
  const printButton = document.createElement("button");
  printButton.innerHTML = "🖨️ Drucken";
  printButton.className = "print-button";
  printButton.style.cssText = `
        position: fixed;
        top: 1rem;
        right: 1rem;
        background: var(--primary-color);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.9rem;
        z-index: 1000;
        transition: background-color 0.2s ease;
    `;

  printButton.addEventListener("mouseenter", () => {
    printButton.style.backgroundColor = "var(--accent-color)";
  });

  printButton.addEventListener("mouseleave", () => {
    printButton.style.backgroundColor = "var(--primary-color)";
  });

  printButton.addEventListener("click", () => {
    window.print();
  });

  document.body.appendChild(printButton);

  // Hide print button on mobile
  if (window.innerWidth <= 768) {
    printButton.style.display = "none";
  }
}

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute("href"));
    if (target) {
      target.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  });
});

// Keyboard shortcuts
document.addEventListener("keydown", function (e) {
  // Ctrl+K or Cmd+K for search
  if ((e.ctrlKey || e.metaKey) && e.key === "k") {
    e.preventDefault();
    const searchInput = document.querySelector(".search-input");
    if (searchInput) {
      searchInput.focus();
    }
  }

  // Escape to close search suggestions
  if (e.key === "Escape") {
    const suggestions = document.querySelector(".search-suggestions");
    if (suggestions) {
      suggestions.style.display = "none";
    }
  }
});

// Table of contents auto-generation
function generateTableOfContents() {
  const headings = document.querySelectorAll("h2, h3, h4");
  if (headings.length < 3) return; // Don't create TOC for short pages

  const toc = document.createElement("div");
  toc.className = "auto-toc";
  toc.innerHTML = "<h3>Inhalt</h3>";

  const list = document.createElement("ul");
  list.style.cssText = `
        list-style-type: none;
        padding-left: 0;
        margin: 1rem 0;
    `;

  headings.forEach((heading, index) => {
    const id = `toc-${index}`;
    heading.id = id;

    const listItem = document.createElement("li");
    listItem.style.cssText = `
            padding: 0.25rem 0;
            padding-left: ${(parseInt(heading.tagName.charAt(1)) - 2) * 1}rem;
        `;

    const link = document.createElement("a");
    link.href = `#${id}`;
    link.textContent = heading.textContent;
    link.style.cssText = `
            color: var(--secondary-color);
            text-decoration: none;
            transition: color 0.2s ease;
        `;

    link.addEventListener("mouseenter", () => {
      link.style.color = "var(--primary-color)";
    });

    link.addEventListener("mouseleave", () => {
      link.style.color = "var(--secondary-color)";
    });

    listItem.appendChild(link);
    list.appendChild(listItem);
  });

  toc.appendChild(list);

  // Insert TOC after the first heading
  const firstHeading = document.querySelector("h1");
  if (firstHeading) {
    firstHeading.parentNode.insertBefore(toc, firstHeading.nextSibling);
  }
}

// Generate TOC on page load
document.addEventListener("DOMContentLoaded", generateTableOfContents);

// Theme switching (if implemented)
function initializeThemeSwitcher() {
  const themeButton = document.createElement("button");
  themeButton.innerHTML = "🌙";
  themeButton.className = "theme-switcher";
  themeButton.title = "Thema wechseln";
  themeButton.style.cssText = `
        position: fixed;
        bottom: 1rem;
        right: 1rem;
        background: var(--primary-color);
        color: white;
        border: none;
        padding: 0.5rem;
        border-radius: 50%;
        cursor: pointer;
        font-size: 1.2rem;
        z-index: 1000;
        width: 3rem;
        height: 3rem;
        transition: background-color 0.2s ease;
    `;

  themeButton.addEventListener("click", function () {
    document.body.classList.toggle("dark-theme");
    this.innerHTML = document.body.classList.contains("dark-theme")
      ? "☀️"
      : "🌙";
  });

  document.body.appendChild(themeButton);
}

// Initialize theme switcher
document.addEventListener("DOMContentLoaded", initializeThemeSwitcher);
