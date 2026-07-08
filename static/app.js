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
  const previous = accessFilter.value;
  const values = new Set();
  hosts.forEach((h) => h.access.forEach((a) => values.add(a)));
  accessFilter.querySelectorAll("option:not(:first-child)").forEach((o) => o.remove());
  [...values].sort().forEach((value) => {
    const opt = document.createElement("option");
    opt.value = value;
    opt.textContent = value;
    accessFilter.appendChild(opt);
  });
  accessFilter.value = previous;
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
      <td><button class="edit-btn" data-ip="${h.ip}" type="button">✎</button></td>
    </tr>
  `).join("");
  countEl.textContent = `${rows.length} / ${hosts.length} hosts`;
}

// --- Ajout / édition ---

const dialog = document.getElementById("host-dialog");
const form = document.getElementById("host-form");
const dialogTitle = document.getElementById("dialog-title");
const dialogError = document.getElementById("dialog-error");
let editingIp = null;

function openDialog(host) {
  dialogError.textContent = "";
  editingIp = host ? host.ip : null;
  dialogTitle.textContent = host ? `Modifier ${host.ip}` : "Ajouter un host";
  form.ip.value = host ? host.ip : "";
  form.name.value = host ? host.name : "";
  form.type.value = host ? host.type : "virtual";
  form.location.value = host ? host.location : "on-prem";
  form.access.value = host ? host.access.join(", ") : "";
  dialog.showModal();
}

document.getElementById("add-host").addEventListener("click", () => openDialog(null));
document.getElementById("dialog-cancel").addEventListener("click", () => dialog.close());

tbody.addEventListener("click", (e) => {
  const btn = e.target.closest(".edit-btn");
  if (!btn) return;
  const host = hosts.find((h) => h.ip === btn.dataset.ip);
  if (host) openDialog(host);
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  dialogError.textContent = "";

  const payload = {
    ip: form.ip.value.trim(),
    name: form.name.value.trim(),
    type: form.type.value,
    location: form.location.value,
    access: form.access.value.split(",").map((a) => a.trim()).filter(Boolean),
  };

  const url = editingIp ? `/api/hosts/${editingIp}` : "/api/hosts";
  const method = editingIp ? "PUT" : "POST";

  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    dialogError.textContent = err.detail || "Erreur lors de l'enregistrement.";
    return;
  }

  const saved = await res.json();
  if (editingIp) {
    hosts = hosts.map((h) => (h.ip === editingIp ? saved : h));
  } else {
    hosts.push(saved);
  }
  dialog.close();
  populateAccessFilter();
  applyFiltersAndSort();
});

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
