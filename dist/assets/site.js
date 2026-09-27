(() => {
  const normalize = value => (value || "").toLocaleLowerCase().trim();

  const schoolCards = [...document.querySelectorAll("[data-school-card]")];
  const schoolSearch = document.querySelector("#schoolSearch");
  const strengthFilter = document.querySelector("#strengthFilter");
  const schoolCount = document.querySelector("#schoolResultCount");
  function filterSchools() {
    if (!schoolCards.length) return;
    const query = normalize(schoolSearch?.value);
    const strength = normalize(strengthFilter?.value);
    let visible = 0;
    schoolCards.forEach(card => {
      const haystack = normalize(card.dataset.search);
      const show = (!query || haystack.includes(query)) && (!strength || haystack.includes(strength));
      card.hidden = !show;
      if (show) visible += 1;
    });
    schoolCount.textContent = `显示 ${visible} 所学校`;
  }
  schoolSearch?.addEventListener("input", filterSchools);
  strengthFilter?.addEventListener("change", filterSchools);

  const facultyCards = [...document.querySelectorAll("[data-faculty-card]")];
  const facultySearch = document.querySelector("#facultySearch");
  const areaFilter = document.querySelector("#areaFilter");
  const publicFilter = document.querySelector("#publicFilter");
  const facultySort = document.querySelector("#facultySort");
  const facultyGrid = document.querySelector("#facultyGrid");
  const facultyReset = document.querySelector("#facultyReset");
  const facultyCount = document.querySelector("#facultyResultCount");
  function filterFaculty() {
    if (!facultyCards.length) return;
    const query = normalize(facultySearch?.value);
    const area = areaFilter?.value || "";
    const publicField = publicFilter?.value || "";
    let visible = 0;
    facultyCards.forEach(card => {
      const publicFields = (card.dataset.public || "").split(" ");
      const show = (!query || normalize(card.dataset.search).includes(query)) &&
        (!area || card.dataset.area === area) &&
        (!publicField || publicFields.includes(publicField));
      card.hidden = !show;
      if (show) visible += 1;
    });
    facultyCount.textContent = `显示 ${visible} 名`;
  }
  function sortFaculty() {
    if (!facultyGrid) return;
    const mode = facultySort?.value || "name";
    const sorted = [...facultyCards].sort((a, b) => {
      if (mode === "completeness") {
        const score = Number(b.dataset.completeness || 0) - Number(a.dataset.completeness || 0);
        if (score) return score;
      }
      return (a.dataset.name || "").localeCompare(b.dataset.name || "", "en");
    });
    sorted.forEach(card => facultyGrid.appendChild(card));
  }
  facultySearch?.addEventListener("input", filterFaculty);
  areaFilter?.addEventListener("change", filterFaculty);
  publicFilter?.addEventListener("change", filterFaculty);
  facultySort?.addEventListener("change", sortFaculty);
  facultyReset?.addEventListener("click", () => {
    if (facultySearch) facultySearch.value = "";
    if (areaFilter) areaFilter.value = "";
    if (publicFilter) publicFilter.value = "";
    if (facultySort) facultySort.value = "name";
    sortFaculty();
    filterFaculty();
    facultySearch?.focus();
  });
  sortFaculty();
})();
