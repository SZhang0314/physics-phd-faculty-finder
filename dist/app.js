(function () {
  "use strict";

  const data = Array.isArray(window.facultyData) ? window.facultyData : [];
  const results = document.querySelector("#results");
  const resultCount = document.querySelector("#result-count");
  const emptyState = document.querySelector("#empty-state");
  const filtersForm = document.querySelector("#filters");
  const searchInput = document.querySelector("#search");
  const fieldFilter = document.querySelector("#field-filter");
  const modeFilter = document.querySelector("#mode-filter");
  const scopeFilter = document.querySelector("#scope-filter");
  const sortFilter = document.querySelector("#sort-filter");
  const emptyReset = document.querySelector("#empty-reset");

  const accents = {
    "量子信息与 AMO": "#6ee7f2",
    "凝聚态与材料": "#ffca6a",
    "粒子与宇宙": "#a99cff",
    "天体与引力": "#8ee8b5"
  };

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function normalize(value) {
    return String(value).toLocaleLowerCase("zh-CN").trim();
  }

  function getFilteredData() {
    const query = normalize(searchInput.value);

    return data
      .filter((person) => {
        const haystack = normalize([
          person.name,
          person.school,
          person.code,
          person.title,
          person.field,
          person.mode,
          person.reason,
          ...person.keywords
        ].join(" "));

        const matchesSearch = !query || haystack.includes(query);
        const matchesField = fieldFilter.value === "all" || person.field === fieldFilter.value;
        const matchesMode = modeFilter.value === "all" || person.mode === modeFilter.value;
        const matchesScope = scopeFilter.value === "us30" || person.qsRank <= 30;
        return matchesSearch && matchesField && matchesMode && matchesScope;
      })
      .sort((a, b) => {
        if (sortFilter.value === "school") return a.school.localeCompare(b.school, "en");
        if (sortFilter.value === "qsRank") return a.qsRank - b.qsRank || a.usRank - b.usRank;
        return a.usRank - b.usRank;
      });
  }

  function cardTemplate(person) {
    const keywords = person.keywords
      .map((keyword) => `<span class="keyword">${escapeHtml(keyword)}</span>`)
      .join("");

    return `
      <article class="faculty-card" style="--accent: ${accents[person.field] || "#6ee7f2"}">
        <div class="card-rank">
          <span class="rank-index">US ${String(person.usRank).padStart(2, "0")}</span>
          <span class="qs-rank">QS ${escapeHtml(person.qsRankLabel)}</span>
        </div>
        <div class="school-line">
          <span class="school-code" aria-hidden="true">${escapeHtml(person.code)}</span>
          <p class="school-name">${escapeHtml(person.school)}</p>
        </div>
        <h3 class="faculty-name">${escapeHtml(person.name)}</h3>
        <p class="faculty-title">${escapeHtml(person.title)}</p>
        <div class="badges">
          <span class="badge">${escapeHtml(person.field)}</span>
          <span class="badge mode">${escapeHtml(person.mode)}</span>
        </div>
        <p class="reason">${escapeHtml(person.reason)}</p>
        <div class="keywords">${keywords}</div>
        <div class="card-footer">
          <span class="verify-label">官方页面核验</span>
          <a class="profile-link" href="${escapeHtml(person.url)}" target="_blank" rel="noreferrer" aria-label="打开 ${escapeHtml(person.name)} 的官方页面">官方主页 ↗</a>
        </div>
      </article>
    `;
  }

  function render() {
    const filtered = getFilteredData();
    results.innerHTML = filtered.map(cardTemplate).join("");
    resultCount.textContent = String(filtered.length);
    results.hidden = filtered.length === 0;
    emptyState.hidden = filtered.length !== 0;
  }

  function resetFilters() {
    filtersForm.reset();
    render();
    searchInput.focus();
  }

  filtersForm.addEventListener("input", render);
  filtersForm.addEventListener("change", render);
  filtersForm.addEventListener("reset", () => window.requestAnimationFrame(render));
  emptyReset.addEventListener("click", resetFilters);

  document.querySelector("#school-count").textContent = String(new Set(data.map((item) => item.school)).size);
  document.querySelector("#faculty-count").textContent = String(data.length);
  render();
})();
