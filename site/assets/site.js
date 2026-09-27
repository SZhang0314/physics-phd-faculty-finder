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
  const facultyCount = document.querySelector("#facultyResultCount");
  function filterFaculty() {
    if (!facultyCards.length) return;
    const query = normalize(facultySearch?.value);
    const area = areaFilter?.value || "";
    let visible = 0;
    facultyCards.forEach(card => {
      const show = (!query || normalize(card.dataset.search).includes(query)) && (!area || card.dataset.area === area);
      card.hidden = !show;
      if (show) visible += 1;
    });
    facultyCount.textContent = `显示 ${visible} 名`;
  }
  facultySearch?.addEventListener("input", filterFaculty);
  areaFilter?.addEventListener("change", filterFaculty);
})();
