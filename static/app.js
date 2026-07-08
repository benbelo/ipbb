let hosts = [];
let sortKey = "name";
let sortDesc = false;

const tbody = document.querySelector("#hosts-table tbody");
const searchInput = document.getElementById("search");
const typeFilter = document.getElementById("filter-type");
const locationFilter = document.getElementById("filter-location");
const accessFilter = document.getElementById("filter-access");
const countEl = document.getElementById("count");

function populateAccessFilter() {
  const values = new Set();
  hosts.forEach((h) => h.access.forEach((a) => values.add(a)));
  [...values].sort().forEach((value) => {
    const opt = document.createElement("option");
    opt.value = value;
    opt.textContent = value;
    accessFilter.appendChild(opt);
  });
}

function applyFiltersAndSort() {
  const search = searchInput.value.trim().toLowerCase();
  const type = typeFilter.value;
  const location = locationFilter.value;
  const access = accessFilter.value;

  let rows = hosts.filter((h) => {
    if (type && h.type !== type) return false;
    if (location && h.location !== location) return false;
    if (access && !h.access.includes(access)) return false;
    if (search && !(h.name.toLowerCase().includes(search) || h.ip.includes(search))) return false;
    return true;
  });

  rows.sort((a, b) => {
    const av = sortKey === "access" ? a.access.join(",") : a[sortKey];
    const bv = sortKey === "access" ? b.access.join(",") : b[sortKey];
    const cmp = String(av).localeCompare(String(bv));
    return sortDesc ? -cmp : cmp;
  });

  render(rows);
}

function render(rows) {
  tbody.innerHTML = rows.map((h) => `
    <tr>
      <td>${h.ip}</td>
      <td>${h.name}</td>
      <td class="tag">${h.type === "virtual" ? "Virtuel" : "Physique"}</td>
      <td class="tag">${h.location === "cloud" ? "Cloud" : "On-prem"}</td>
      <td>${h.access.map((a) => `<span class="badge">${a}</span>`).join("")}</td>
    </tr>
  `).join("");
  countEl.textContent = `${rows.length} / ${hosts.length} hosts`;
}

document.querySelectorAll("th[data-key]").forEach((th) => {
  th.addEventListener("click", () => {
    const key = th.dataset.key;
    if (sortKey === key) {
      sortDesc = !sortDesc;
    } else {
      sortKey = key;
      sortDesc = false;
    }
    document.querySelectorAll("th[data-key]").forEach((el) => el.classList.remove("sorted", "desc"));
    th.classList.add("sorted");
    if (sortDesc) th.classList.add("desc");
    applyFiltersAndSort();
  });
});

[searchInput, typeFilter, locationFilter, accessFilter].forEach((el) => {
  el.addEventListener("input", applyFiltersAndSort);
});

fetch("/api/hosts")
  .then((res) => res.json())
  .then((data) => {
    hosts = data;
    populateAccessFilter();
    applyFiltersAndSort();
  });
