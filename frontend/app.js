/* Remnant frontend preview. All sample data stays in this page; no API is required. */
(() => {
  "use strict";

  const initialSupplies = [
    { id: "water", name: "Drinking water", code: "H₂O-001", category: "Life support", unit: "L", quantity: 192, daily: 24, volume: 1, icon: "droplet" },
    { id: "oxygen", name: "Oxygen", code: "O₂-002", category: "Life support", unit: "kg", quantity: 72, daily: 12, volume: 2, icon: "wind" },
    { id: "food", name: "Food rations", code: "NTR-003", category: "Nutrition", unit: "meals", quantity: 324, daily: 18, volume: 0.7, icon: "food" },
    { id: "batteries", name: "Battery packs", code: "PWR-004", category: "Power", unit: "packs", quantity: 12, daily: 4, volume: 2, icon: "battery" },
    { id: "filters", name: "CO₂ scrubber filters", code: "AIR-005", category: "Life support", unit: "filters", quantity: 18, daily: 1.5, volume: 0.8, icon: "filter" },
    { id: "medical", name: "Medical kits", code: "MED-006", category: "Medical", unit: "kits", quantity: 16, daily: 0.2, volume: 1.2, icon: "medical" },
    { id: "fuel", name: "Rover fuel", code: "RVR-007", category: "Surface operations", unit: "L", quantity: 180, daily: 5, volume: 1, icon: "fuel" },
    { id: "parts", name: "Spare components", code: "ENG-008", category: "Engineering", unit: "parts", quantity: 42, daily: 0.4, volume: 3, icon: "tools" },
  ];
  const initialShipments = [
    { id: "CRG-008", name: "Lunar Cargo 08", origin: "Gateway → Artemis Outpost", day: 46, cargo: { water: 240, oxygen: 120 } },
    { id: "CRG-009", name: "Lunar Cargo 09", origin: "Earth orbit → Artemis Outpost", day: 52, cargo: { food: 360, filters: 24 } },
  ];
  const TARGET_DAYS = 21;
  const STORAGE_CAPACITY = 1800; // Illustrative storage volume in litres, including packaging.
  const $ = (id) => document.getElementById(id);
  const number = (value) => new Intl.NumberFormat("en-CA", { maximumFractionDigits: 1 }).format(value);
  const daysLeft = (item) => item.daily > 0 ? item.quantity / item.daily : Infinity;
  const status = (item) => daysLeft(item) <= 3 ? "critical" : daysLeft(item) <= 7 ? "watch" : "healthy";
  const statusLabel = { critical: "Critical", watch: "Watch list", healthy: "Healthy" };
  let supplies, shipments, day, draft;
  let activeFilter = "all";
  let editingId = null;
  let toastTimer;

  // Small, consistent line icons. Kept inline so the preview works offline.
  const paths = {
    orbit: '<circle cx="12" cy="12" r="5"/><ellipse cx="12" cy="12" rx="11" ry="4" transform="rotate(-35 12 12)"/><circle cx="20" cy="6" r="1.5" fill="currentColor" stroke="none"/>',
    dashboard: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    box: '<path d="m3 7 9-4 9 4v10l-9 4-9-4zM3 7l9 5 9-5M12 12v9M7.5 5l9 5"/>',
    route: '<circle cx="5" cy="5" r="2"/><circle cx="19" cy="19" r="2"/><path d="M7 5h9a4 4 0 0 1 0 8H8a3 3 0 0 0 0 6h9"/>',
    rocket: '<path d="M4 16l4-1 1-5c3-5 6-7 12-7 0 6-2 9-7 12l-5 1-1 4-4-4zM7 17l-3 4M9 10 4 9l-2 4 4 1M14 15l1 5 4-2-1-5"/><circle cx="16" cy="8" r="2"/>',
    reset: '<path d="M3 10a9 9 0 1 1 2 8M3 4v6h6"/>',
    play: '<path d="m8 5 11 7-11 7z"/>',
    users: '<circle cx="9" cy="8" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6M21 21v-3a6 6 0 0 0-4-5"/>',
    moon: '<path d="M20.9 13A9 9 0 0 1 11 3.1 9 9 0 1 0 20.9 13z"/>',
    arrow: '<path d="M4 12h16m-6-6 6 6-6 6"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7v.01"/>',
    calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4M17 3v4M3 11h18M8 15h2M14 15h2"/>',
    download: '<path d="M12 3v12m-5-5 5 5 5-5M4 16v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4"/>',
    search: '<circle cx="10" cy="10" r="7"/><path d="m15 15 6 6"/>',
    droplet: '<path d="M12 3c-3 4-7 8-7 12a7 7 0 0 0 14 0c0-4-4-8-7-12zM8 15a4 4 0 0 0 4 4"/>',
    wind: '<path d="M3 8h12a3 3 0 1 0-3-3M2 12h17a3 3 0 1 1-3 3M4 16h5a3 3 0 1 1-3 3"/>',
    food: '<path d="M5 3v6a2 2 0 0 0 4 0V3M7 3v18M17 3c-3 3-3 8 0 9h2M19 3v18"/>',
    battery: '<rect x="2" y="6" width="18" height="12" rx="2"/><path d="M23 10v4M6 10v4M10 10v4M14 10v4"/>',
    filter: '<path d="M3 4h18l-7 8v7l-4 2v-9z"/>',
    medical: '<rect x="3" y="6" width="18" height="15" rx="2"/><path d="M9 6V3h6v3M12 10v7M8.5 13.5h7"/>',
    fuel: '<path d="M3 21V5a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v16M1 21h15M3 10h11M14 13h3v5a2 2 0 0 0 4 0v-8l-4-5"/>',
    tools: '<path d="m14 6 4 4M3 21l8-8M14 3a6 6 0 0 0-5 8L3 17a3 3 0 0 0 4 4l6-6a6 6 0 0 0 8-7l-4 4-5-5 4-4z"/>',
    alert: '<path d="m10.3 4-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3l-8-14a2 2 0 0 0-3.4 0zM12 9v5M12 17v.01"/>',
    shield: '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6zM8 12l3 3 5-6"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    check: '<path d="m5 12 4 4L19 6"/>',
  };
  function icon(name) {
    return `<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.box}</svg>`;
  }
  document.querySelectorAll("[data-icon]").forEach((element) => { element.innerHTML = icon(element.dataset.icon); });

  function reset() {
    supplies = initialSupplies.map((item) => ({ ...item }));
    shipments = initialShipments.map((item) => ({ ...item, cargo: { ...item.cargo }, received: false }));
    day = 42;
    draft = new Set();
    activeFilter = "all";
    $("inventory-search").value = "";
    $("forecast-range").value = "14";
    render();
  }

  function priorities() {
    return supplies.filter((item) => status(item) !== "healthy").map((item) => {
      const incoming = shipments.filter((shipment) => !shipment.received && shipment.cargo[item.id] && shipment.day <= day + TARGET_DAYS);
      const inboundQuantity = incoming.reduce((sum, shipment) => sum + shipment.cargo[item.id], 0);
      const firstArrival = incoming.length ? Math.min(...incoming.map((shipment) => shipment.day - day)) : null;
      // Cover the 21-day target and any shortage before the first scheduled arrival.
      const bridge = firstArrival === null ? 0 : Math.max(0, firstArrival * item.daily - item.quantity);
      const quantity = Math.ceil(Math.max(0, TARGET_DAYS * item.daily - item.quantity - inboundQuantity, bridge));
      return { ...item, quantityToOrder: quantity, urgent: daysLeft(item) <= 3 || bridge > 0, inboundQuantity };
    }).sort((a, b) => Number(b.urgent) - Number(a.urgent) || daysLeft(a) - daysLeft(b));
  }

  function renderSummary() {
    const safe = supplies.filter((item) => status(item) === "healthy").length;
    const critical = supplies.filter((item) => status(item) === "critical").length;
    const watch = supplies.filter((item) => status(item) === "watch").length;
    const next = shipments.find((shipment) => !shipment.received);
    const used = supplies.reduce((sum, item) => sum + item.quantity * item.volume, 0);
    const remaining = STORAGE_CAPACITY - used;
    const cards = [
      { color: "blue", label: "Supply readiness", value: `${Math.round(safe / supplies.length * 100)}<small>%</small>`, detail: `${safe} of ${supplies.length} supplies above 7 days`, icon: "shield" },
      { color: "red", label: "Critical shortages", value: `${critical}<small>${critical === 1 ? "supply" : "supplies"}</small>`, detail: `${watch} more on the watch list`, icon: "alert", extra: "critical-summary" },
      { color: "azure", label: "Next delivery", value: next ? `${next.day - day}<small>days</small>` : "—", detail: next ? `${next.name} · Mission day ${next.day}` : "All scheduled cargo received", icon: "rocket" },
      { color: "purple", label: remaining >= 0 ? "Storage available" : "Storage exceeded", value: `${number(Math.abs(remaining) / STORAGE_CAPACITY * 100)}<small>%</small>`, detail: `${number(Math.abs(remaining))} L ${remaining >= 0 ? "free" : "over capacity"} / ${number(STORAGE_CAPACITY)} L`, icon: "box" },
    ];
    $("summary-cards").innerHTML = cards.map((card) => `<div class="col-12 col-sm-6 col-xl-3"><article class="card card-gradient card-gradient-${card.color} summary-card h-100"><div class="card-body"><div class="summary-label">${card.label}<span class="text-${card.color}">${icon(card.icon)}</span></div><div class="summary-value ${card.extra ? "text-danger-emphasis" : ""}">${card.value}</div><div class="summary-detail text-secondary mt-2">${card.detail}</div></div></article></div>`).join("");
    const lowest = [...supplies].sort((a, b) => daysLeft(a) - daysLeft(b))[0];
    const alerts = critical + watch;
    $("shortage-alert").className = `alert alert-${critical ? "danger" : alerts ? "warning" : "success"}`;
    $("shortage-alert").innerHTML = `<div class="d-flex flex-wrap align-items-center gap-3"><span class="d-flex">${icon(alerts ? "alert" : "check")}</span><div class="flex-fill">${alerts ? `<strong>${lowest.name} needs attention.</strong> ${number(daysLeft(lowest))} days of supply remaining. ${critical ? "Prioritize an early resupply." : "Plan ahead to maintain your reserve."}` : "All supplies have more than 7 days of coverage."}</div><a class="alert-link d-inline-flex align-items-center gap-2" href="#resupply">View resupply plan ${icon("arrow")}</a></div>`;
    $("mission-day").textContent = String(day).padStart(3, "0");
    $("sidebar-day").textContent = String(day).padStart(3, "0");
    $("nav-alert-count").textContent = alerts;
    $("all-count").textContent = supplies.length;
    $("critical-count").textContent = critical;
    $("watch-count").textContent = watch;
    $("forecast-note").textContent = next ? `Next cargo arrival in ${next.day - day} days` : "All scheduled cargo received";
    $("advance-day").disabled = day >= 180;
  }

  function renderInventory() {
    const query = $("inventory-search").value.trim().toLowerCase();
    const visible = supplies.filter((item) => (activeFilter === "all" || status(item) === activeFilter) && `${item.name} ${item.code} ${item.category}`.toLowerCase().includes(query));
    document.querySelectorAll("[data-filter]").forEach((button) => {
      button.classList.toggle("active", button.dataset.filter === activeFilter);
      button.setAttribute("aria-pressed", String(button.dataset.filter === activeFilter));
    });
    $("inventory-rows").innerHTML = visible.length ? visible.map((item) => {
      const health = status(item);
      const remaining = daysLeft(item);
      const color = { critical: "red", watch: "yellow", healthy: "green" }[health];
      const emphasis = { critical: "danger", watch: "warning", healthy: "success" }[health];
      return `<tr><td><div class="d-flex align-items-center gap-3"><span class="avatar bg-secondary-lt text-secondary">${icon(item.icon)}</span><div><div class="fw-medium">${item.name}</div><div class="text-secondary inventory-table-secondary">${item.code} · ${item.category}</div></div></div></td><td><span class="fw-medium">${number(item.quantity)}</span> <span class="text-secondary inventory-table-secondary">${item.unit}</span></td><td>${number(item.daily)} <span class="text-secondary inventory-table-secondary">${item.unit}/day</span></td><td class="supply-days"><span class="text-${emphasis}-emphasis fw-medium">${Number.isFinite(remaining) ? number(remaining) + " days" : "No daily use"}</span><div class="progress progress-sm" aria-hidden="true"><span class="progress-bar bg-${color}" style="width:${Math.min(100, remaining / TARGET_DAYS * 100)}%"></span></div></td><td><span class="badge bg-${color}-lt text-${emphasis}-emphasis">${statusLabel[health]}</span></td><td class="text-end"><button class="btn" data-edit="${item.id}" aria-label="Update ${item.name}">Update</button></td></tr>`;
    }).join("") : '<tr><td colspan="6" class="text-center text-secondary p-4">No supplies match these filters. Try a different search or select All supplies.</td></tr>';
    $("inventory-result-count").textContent = `Showing ${visible.length} of ${supplies.length} supplies`;
  }

  function renderPriorities() {
    const items = priorities();
    draft.forEach((id) => { if (!items.some((item) => item.id === id && item.quantityToOrder > 0)) draft.delete(id); });
    $("recommendations").innerHTML = items.length ? items.map((item, index) => {
      const added = draft.has(item.id);
      const message = item.quantityToOrder === 0 ? "Covered by scheduled cargo. Monitor until arrival." : `${item.urgent ? "Expedite" : "Replenish"} before day ${number(day + daysLeft(item))}.${item.inboundQuantity ? " Scheduled cargo accounted for." : " Restore a 21-day reserve."}`;
      return `<article class="list-group-item"><div class="d-flex gap-3"><span class="avatar avatar-sm bg-${item.urgent ? "red" : "yellow"}-lt text-${item.urgent ? "danger" : "warning"}-emphasis">${String(index + 1).padStart(2, "0")}</span><div class="priority-copy"><div class="priority-heading"><h3 class="h3 mb-0">${item.name}</h3><span class="badge bg-${item.urgent ? "red" : "yellow"}-lt text-${item.urgent ? "danger" : "warning"}-emphasis">${number(daysLeft(item))} days left</span></div><p class="text-secondary small my-2">${message}</p><div class="priority-action"><strong>${item.quantityToOrder ? `+${number(item.quantityToOrder)} ${item.unit} recommended` : "Inbound coverage"}</strong>${item.quantityToOrder ? `<button class="btn ${added ? "" : "btn-outline-primary"}" data-draft="${item.id}" aria-pressed="${added}" aria-label="${added ? "Remove" : "Add"} ${item.name} ${added ? "from" : "to"} draft">${icon(added ? "check" : "plus")}${added ? "Added" : "Add to draft"}</button>` : '<a class="btn" href="#deliveries">View cargo</a>'}</div></div></div></article>`;
    }).join("") : '<div class="text-center text-secondary p-4">All essentials are above the reserve threshold.<br>No immediate resupply needed.</div>';
    $("manifest-summary").textContent = draft.size ? `${draft.size} ${draft.size === 1 ? "item" : "items"} in draft · not dispatched` : "No items in draft manifest";
    $("download-manifest").disabled = draft.size === 0;
  }

  function renderForecast() {
    const horizon = Number($("forecast-range").value);
    const series = ["water", "oxygen", "food"].map((id) => {
      const item = supplies.find((supply) => supply.id === id);
      let quantity = item.quantity;
      const values = [quantity / (item.daily * TARGET_DAYS) * 100];
      for (let offset = 1; offset <= horizon; offset++) {
        quantity = Math.max(0, quantity - item.daily);
        shipments.filter((shipment) => !shipment.received && shipment.day === day + offset).forEach((shipment) => { quantity += shipment.cargo[id] || 0; });
        values.push(quantity / (item.daily * TARGET_DAYS) * 100);
      }
      return { id, name: item.name, values };
    });
    const max = Math.max(100, Math.ceil(Math.max(...series.flatMap((line) => line.values)) / 50) * 50);
    // Match the SVG to its actual container so labels stay legible on every screen.
    const width = Math.max(280, $("forecast-chart").clientWidth);
    const height = 280, left = 53, right = 16, top = 27, bottom = 32;
    const x = (offset) => left + offset / horizon * (width - left - right);
    const y = (percent) => height - bottom - percent / max * (height - top - bottom);
    let content = "";
    for (let tick = 0; tick <= 4; tick++) {
      const percent = max / 4 * tick;
      content += `<line x1="${left}" x2="${width - right}" y1="${y(percent)}" y2="${y(percent)}" stroke="var(--tblr-border-color)"/><text x="${left - 9}" y="${y(percent) + 4}" text-anchor="end" fill="var(--tblr-secondary)" font-size="13">${number(percent)}%</text>`;
    }
    content += `<line x1="${left}" x2="${width - right}" y1="${y(100 / 3)}" y2="${y(100 / 3)}" stroke="var(--tblr-yellow)" stroke-dasharray="5 4"/>`;
    const tickCount = width < 480 ? 4 : 7;
    for (let tick = 0; tick <= tickCount; tick++) {
      const offset = horizon / tickCount * tick;
      content += `<text x="${x(offset)}" y="${height - 6}" text-anchor="middle" fill="var(--tblr-secondary)" font-size="13">D${Math.round(day + offset)}</text>`;
    }
    shipments.filter((shipment) => !shipment.received && shipment.day <= day + horizon).forEach((shipment) => {
      const position = x(shipment.day - day);
      const nearEnd = position > width - 100;
      content += `<line x1="${position}" x2="${position}" y1="${top}" y2="${height - bottom}" stroke="var(--tblr-secondary)" stroke-dasharray="3 4"/><text x="${position + (nearEnd ? -5 : 5)}" y="${top - 9}" text-anchor="${nearEnd ? "end" : "start"}" fill="var(--tblr-secondary)" font-size="12">${width < 480 ? "Cargo" : "Cargo arrival"}</text>`;
    });
    const colors = { water: "var(--tblr-blue)", oxygen: "var(--tblr-purple)", food: "var(--tblr-green)" };
    series.forEach((line) => {
      const points = line.values.map((value, index) => `${x(index)},${y(value)}`).join(" ");
      content += `<polyline points="${points}" fill="none" stroke="${colors[line.id]}" stroke-width="2.5" stroke-linejoin="round"><title>${line.name}: ${number(line.values[0])}% now, ${number(line.values.at(-1))}% in ${horizon} days</title></polyline><circle cx="${x(0)}" cy="${y(line.values[0])}" r="3.5" fill="${colors[line.id]}" stroke="white" stroke-width="2"/>`;
    });
    $("forecast-chart").innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="chart-title chart-description"><title id="chart-title">${horizon}-day supply forecast</title><desc id="chart-description">Water, oxygen and food as percentages of a 21-day supply target. Scheduled cargo increases stock on arrival. The dashed horizontal line marks a 7-day reserve. Draft requests are excluded.</desc>${content}</svg>`;
  }

  function renderShipments() {
    $("shipment-list").innerHTML = shipments.map((shipment) => `<div class="col-12 col-lg-6"><article class="card h-100"><div class="card-body"><div class="d-flex flex-wrap align-items-start gap-3"><span class="avatar bg-blue-lt text-blue">${icon("rocket")}</span><div class="flex-fill"><h3 class="h3 mb-1">${shipment.name}</h3><p class="text-secondary small mb-2">${shipment.id} · ${shipment.origin}</p></div><span class="badge bg-${shipment.received ? "green" : "blue"}-lt text-${shipment.received ? "success" : "primary"}-emphasis">${shipment.received ? "Received" : `${shipment.day - day} days · In transit`}</span></div><div class="d-flex flex-wrap gap-2 mt-2">${Object.entries(shipment.cargo).map(([id, quantity]) => { const item = supplies.find((supply) => supply.id === id); return `<span class="badge bg-secondary-lt text-secondary">${number(quantity)} ${item.unit} ${item.name.toLowerCase()}</span>`; }).join("")}</div></div><div class="card-footer text-secondary">${shipment.received ? "Received on" : "Scheduled arrival:"} mission day ${shipment.day}</div></article></div>`).join("");
  }

  function render() {
    renderSummary();
    renderInventory();
    renderPriorities();
    renderForecast();
    renderShipments();
  }
  function toast(message) {
    clearTimeout(toastTimer);
    $("toast").textContent = message;
    $("toast").hidden = false;
    toastTimer = setTimeout(() => { $("toast").hidden = true; }, 4500);
  }
  function downloadCSV(filename, rows) {
    const csv = rows.map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(",")).join("\r\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  $("simulate-shortage").addEventListener("click", () => {
    supplies.find((item) => item.id === "water").quantity = 48;
    render();
    toast("Water is down to 2 days. An expedited resupply is now recommended.");
  });
  $("reset-demo").addEventListener("click", () => { reset(); toast("Sample mission reset. All demo changes cleared."); });
  $("advance-day").addEventListener("click", () => {
    if (day >= 180) return;
    supplies.forEach((item) => { item.quantity = Math.max(0, Math.round((item.quantity - item.daily) * 10) / 10); });
    day++;
    const arrivals = shipments.filter((shipment) => !shipment.received && shipment.day <= day);
    arrivals.forEach((shipment) => {
      Object.entries(shipment.cargo).forEach(([id, quantity]) => { supplies.find((item) => item.id === id).quantity += quantity; });
      shipment.received = true;
    });
    render();
    toast(arrivals.length ? `Day ${day}: cargo received and onboard inventory updated.` : `Advanced to day ${day}. Sample daily consumption applied.`);
  });
  $("forecast-range").addEventListener("change", renderForecast);
  $("inventory-search").addEventListener("input", renderInventory);
  document.querySelectorAll("[data-filter]").forEach((button) => button.addEventListener("click", () => { activeFilter = button.dataset.filter; renderInventory(); }));
  $("recommendations").addEventListener("click", (event) => {
    const button = event.target.closest("[data-draft]");
    if (!button) return;
    const id = button.dataset.draft;
    draft.has(id) ? draft.delete(id) : draft.add(id);
    renderPriorities();
    $("recommendations").querySelector(`[data-draft="${id}"]`)?.focus();
  });
  $("inventory-rows").addEventListener("click", (event) => {
    const button = event.target.closest("[data-edit]");
    if (!button) return;
    editingId = button.dataset.edit;
    const item = supplies.find((supply) => supply.id === editingId);
    $("edit-title").textContent = item.name;
    $("quantity-label").textContent = `Onboard quantity (${item.unit})`;
    $("supply-quantity").value = item.quantity;
    $("edit-dialog").showModal();
    $("supply-quantity").focus();
    $("supply-quantity").select();
  });
  ["close-dialog", "cancel-edit"].forEach((id) => $(id).addEventListener("click", () => $("edit-dialog").close()));
  $("edit-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const quantity = Number($("supply-quantity").value);
    if (!Number.isFinite(quantity) || quantity < 0 || quantity > 1000000 || !$("edit-form").reportValidity()) return;
    const item = supplies.find((supply) => supply.id === editingId);
    item.quantity = quantity;
    $("edit-dialog").close();
    render();
    $("inventory-rows").querySelector(`[data-edit="${editingId}"]`)?.focus();
    toast(`${item.name} updated. Alerts and recommendations recalculated.`);
  });
  $("export-inventory").addEventListener("click", () => downloadCSV(`remnant-inventory-day-${day}.csv`, [
    ["Supply", "Category", "Quantity", "Unit", "Daily consumption", "Days remaining", "Status"],
    ...supplies.map((item) => [item.name, item.category, item.quantity, item.unit, item.daily, number(daysLeft(item)), statusLabel[status(item)]]),
  ]));
  $("download-manifest").addEventListener("click", () => downloadCSV(`remnant-draft-day-${day}.csv`, [
    ["Supply", "Recommended quantity", "Unit", "Priority", "Mission day", "State"],
    ...priorities().filter((item) => draft.has(item.id)).map((item) => [item.name, item.quantityToOrder, item.unit, item.urgent ? "Expedite" : "Replenish", day, "Draft - not dispatched"]),
  ]));
  function updateNavigation() {
    const section = location.hash.slice(1) || "overview";
    const names = { overview: "Overview", inventory: "Inventory", resupply: "Resupply planning", deliveries: "Deliveries" };
    $("page-location").textContent = names[section] || "Overview";
    document.querySelectorAll("[data-nav]").forEach((link) => {
      const active = link.dataset.nav === section;
      link.closest(".nav-item").classList.toggle("active", active);
      active ? link.setAttribute("aria-current", "location") : link.removeAttribute("aria-current");
    });
  }
  window.addEventListener("hashchange", updateNavigation);
  document.querySelectorAll("[data-nav]").forEach((link) => link.addEventListener("click", () => {
    if (window.matchMedia("(max-width: 991.98px)").matches) {
      window.tabler?.Collapse?.getOrCreateInstance($("sidebar-menu")).hide();
    }
  }));
  reset();
  updateNavigation();
  let chartWidth = $("forecast-chart").clientWidth;
  new ResizeObserver(([entry]) => {
    const width = Math.round(entry.contentRect.width);
    if (width !== chartWidth) {
      chartWidth = width;
      renderForecast();
    }
  }).observe($("forecast-chart"));
})();
