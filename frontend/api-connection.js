/* Resolve local file previews without changing the served dashboard's API. */
function dashboardApiCandidates(protocol, override) {
  if (override !== null && override !== undefined) return [override.replace(/\/+$/, "")];
  return protocol === "file:" ? ["http://localhost:8000", "http://127.0.0.1:8080"] : [""];
}

async function findDashboardApi(bases, {
  fetchImpl = globalThis.fetch.bind(globalThis), timeoutMs = 2500,
} = {}) {
  for (const base of bases) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetchImpl(`${base}/api/dashboard`, {
        cache: "no-store", signal: controller.signal,
      });
      if (!response.ok) continue;
      const data = await response.json();
      // Another local app can return HTML or unrelated JSON with HTTP 200.
      if (!Array.isArray(data.metrics) || typeof data.phase !== "string"
          || typeof data.link !== "boolean" || !Array.isArray(data.checklist_items)) continue;
      return base;
    } catch {
      // The next known local address may be the running Remnant backend.
    } finally {
      clearTimeout(timeout);
    }
  }
  throw new Error(`Start the Remnant backend and open its dashboard URL. Tried: ${bases.join(", ")}`);
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { dashboardApiCandidates, findDashboardApi };
}
