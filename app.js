let regions = [
  { code: "NG", name: "Nigeria", count: 39, x: 49, y: 61 },
  { code: "US", name: "United States", count: 82, x: 23, y: 44 },
  { code: "CA", name: "Canada", count: 21, x: 25, y: 31 },
  { code: "BR", name: "Brazil", count: 34, x: 38, y: 69 },
  { code: "GB", name: "United Kingdom", count: 28, x: 48, y: 36 },
  { code: "DE", name: "Germany", count: 31, x: 53, y: 40 },
  { code: "ZA", name: "South Africa", count: 17, x: 55, y: 75 },
  { code: "IN", name: "India", count: 44, x: 69, y: 55 },
  { code: "JP", name: "Japan", count: 24, x: 84, y: 45 },
  { code: "AU", name: "Australia", count: 19, x: 84, y: 76 },
];

const map = document.querySelector("#map");
const select = document.querySelector("#country");
const memo = document.querySelector("#memo");
const toast = document.querySelector("#toast");

regions.forEach(({ code, name }) => select.add(new Option(name, code)));
select.value = "NG";

function renderMap() {
  map.innerHTML = `<svg class="world" viewBox="0 0 1200 500" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
    <path d="M70 95l90-45 90 20 42 57-33 48-67-7-30 48-67-8-43-58zM276 235l63 18 45 71-12 115-43 25-28-94-41-52zM449 79l78-34 93 16 56 46-30 39-59-3-29 52-75-8-44-55zM520 211l70-7 62 49 10 71-57 31-34-45-50-19zM690 157l99-5 90 29 78 69-18 53-95-17-59 42-75-23-39-71zM777 316l65 5 45 45-24 70-89-21-29-60zM938 365l119-12 69 38-19 58-132-6-54-45z" />
  </svg>`;
  regions.filter((region) => region.count > 0).forEach((region) => {
  const signal = document.createElement("button");
  signal.className = "signal-dot";
  signal.style.setProperty("--x", `${region.x}%`);
  signal.style.setProperty("--y", `${region.y}%`);
  signal.style.setProperty("--size", `${Math.max(14, Math.min(28, region.count / 2))}px`);
  signal.setAttribute("aria-label", `${region.name}: ${region.count} anonymous signals`);
  signal.innerHTML = `<span class="pulse"></span><span class="tooltip"><b>${region.name}</b>${region.count} anonymous signals</span>`;
    map.append(signal);
  });
  document.querySelector("#total-count").textContent = regions.reduce((sum, region) => sum + region.count, 0).toLocaleString();
  document.querySelector("#country-count").textContent = regions.filter((region) => region.count > 0).length;
}

renderMap();

const apiBase = (window.HOLDER_MAP_CONFIG && window.HOLDER_MAP_CONFIG.apiBase) || "";

async function loadAggregateCounts() {
  try {
    const [mapResponse, statsResponse] = await Promise.all([fetch(`${apiBase}/api/map`), fetch(`${apiBase}/api/stats`)]);
    if (!mapResponse.ok || !statsResponse.ok) return;
    const mapData = await mapResponse.json();
    const stats = await statsResponse.json();
    const counts = new Map(mapData.regions.map((region) => [region.code, region.count]));
    regions = regions.map((region) => ({ ...region, count: counts.get(region.code) || 0 }));
    renderMap();
    document.querySelector("#total-count").textContent = stats.totalSignals.toLocaleString();
    document.querySelector("#country-count").textContent = stats.countriesRepresented;
  } catch (_) {
    // GitHub Pages has no API; leave the clearly-labelled prototype data visible.
  }
}

loadAggregateCounts();

select.addEventListener("change", () => { memo.textContent = `HOLDERMAP:${select.value}`; });
document.querySelector("#copy-memo").addEventListener("click", async () => {
  try { await navigator.clipboard.writeText(memo.textContent); toast.textContent = "Memo copied — use it only with a shielded receipt."; }
  catch { toast.textContent = "Copy the memo shown above."; }
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2800);
});
