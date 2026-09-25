const api = "/api/v1";
const state = { products: [], warehouses: [], inventory: [] };

const $ = (selector) => document.querySelector(selector);

function showNotice(message, isError = false) {
  const notice = $("#notice");
  notice.textContent = message;
  notice.classList.toggle("error", isError);
  notice.hidden = false;
  window.clearTimeout(showNotice.timer);
  showNotice.timer = window.setTimeout(() => { notice.hidden = true; }, 4200);
}

async function request(path, options = {}) {
  const response = await fetch(`${api}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    let detail = "Request failed";
    try { detail = (await response.json()).detail || detail; } catch (_) { /* empty response */ }
    throw new Error(detail);
  }
  return response.status === 204 ? null : response.json();
}

function renderSelectors() {
  $("#product-select").innerHTML = '<option value="">Select product</option>' + state.products
    .map((product) => `<option value="${product.id}">${escapeHtml(product.name)} (${escapeHtml(product.sku)})</option>`).join("");
  $("#warehouse-select").innerHTML = '<option value="">Select warehouse</option>' + state.warehouses
    .map((warehouse) => `<option value="${warehouse.id}">${escapeHtml(warehouse.name)}</option>`).join("");
}

function renderStats() {
  $("#product-count").textContent = state.products.length;
  $("#warehouse-count").textContent = state.warehouses.length;
  $("#position-count").textContent = state.inventory.length;
  const lowStock = state.inventory.filter((item) => item.quantity <= productById(item.product_id).reorder_level);
  $("#low-stock-count").textContent = lowStock.length;
  $("#inventory-status").textContent = `${state.inventory.length} position${state.inventory.length === 1 ? "" : "s"}`;
}

function renderInventory() {
  const table = $("#inventory-table");
  if (!state.inventory.length) {
    table.innerHTML = '<tr><td colspan="5" class="empty-state">No stock positions yet. Add a product and adjust its quantity.</td></tr>';
    return;
  }
  table.innerHTML = state.inventory.map((item) => {
    const product = productById(item.product_id);
    const warehouse = state.warehouses.find((entry) => entry.id === item.warehouse_id);
    const low = item.quantity <= product.reorder_level;
    return `<tr><td>${escapeHtml(product.name)}</td><td class="sku">${escapeHtml(product.sku)}</td><td>${escapeHtml(warehouse?.name || `Warehouse #${item.warehouse_id}`)}</td><td class="quantity">${item.quantity}</td><td><span class="signal ${low ? "low" : "ok"}">${low ? "Reorder" : "Healthy"}</span></td></tr>`;
  }).join("");
}

function renderWarehouses() {
  const list = $("#warehouse-list");
  list.innerHTML = state.warehouses.length ? state.warehouses.map((warehouse) => `<div class="warehouse-item"><strong>${escapeHtml(warehouse.name)}</strong><small>${escapeHtml(warehouse.location || "Location not set")}</small></div>`).join("") : '<div class="empty-state">No warehouses yet.</div>';
}

function productById(id) { return state.products.find((product) => product.id === id) || { name: "Unknown product", sku: "", reorder_level: 0 }; }
function escapeHtml(value) { return String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[char]); }

async function refresh() {
  try {
    [state.products, state.warehouses, state.inventory] = await Promise.all([
      request("/products"), request("/warehouses"), request("/inventory"),
    ]);
    renderStats(); renderSelectors(); renderInventory(); renderWarehouses();
    $("#last-updated").textContent = `Synced ${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
  } catch (error) { showNotice(error.message, true); }
}

$("#product-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  try {
    await request("/products", { method: "POST", body: JSON.stringify({ sku: data.get("sku"), name: data.get("name"), description: data.get("description") || null, reorder_level: Number(data.get("reorder_level")) }) });
    form.reset(); showNotice("Product added to the catalog."); await refresh();
  } catch (error) { showNotice(error.message, true); }
});

$("#warehouse-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  try {
    await request("/warehouses", { method: "POST", body: JSON.stringify({ name: data.get("name"), location: data.get("location") || null }) });
    form.reset(); showNotice("Warehouse added."); await refresh();
  } catch (error) { showNotice(error.message, true); }
});

$("#adjustment-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  try {
    await request("/inventory/adjustments", { method: "POST", body: JSON.stringify({ product_id: Number(data.get("product_id")), warehouse_id: Number(data.get("warehouse_id")), quantity_delta: Number(data.get("quantity_delta")), reason: data.get("reason") || null }) });
    form.reset(); showNotice("Stock adjustment applied."); await refresh();
  } catch (error) { showNotice(error.message, true); }
});

$("#refresh-button").addEventListener("click", refresh);
refresh();
