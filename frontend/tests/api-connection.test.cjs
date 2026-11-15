const { test } = require("node:test");
const assert = require("node:assert/strict");
const { dashboardApiCandidates, findDashboardApi } = require("../api-connection.js");

const dashboard = { metrics: [], phase: "orbit", link: true, checklist_items: [] };
const reply = (status, data) => ({ ok: status === 200, json: async () => data });

test("HTTP and HTTPS dashboards keep using their own server", () => {
  assert.deepEqual(dashboardApiCandidates("http:"), [""]);
  assert.deepEqual(dashboardApiCandidates("https:"), [""]);
});

test("direct-file previews try the default API and the alternate local port", () => {
  assert.deepEqual(dashboardApiCandidates("file:"), ["http://localhost:8000", "http://127.0.0.1:8080"]);
});

test("an explicit backend, including same-origin, takes priority", () => {
  assert.deepEqual(dashboardApiCandidates("file:", "http://localhost:9000/"), ["http://localhost:9000"]);
  assert.deepEqual(dashboardApiCandidates("file:", ""), [""]);
});

test("a missing mission API on port 8000 falls back to the working backend", async () => {
  const calls = [];
  const base = await findDashboardApi(dashboardApiCandidates("file:"), {
    fetchImpl: async (url, options) => {
      calls.push(url);
      assert.equal(options.headers, undefined);  // GET probes do not need CORS preflight.
      return calls.length === 1 ? reply(404) : reply(200, dashboard);
    },
  });
  assert.equal(base, "http://127.0.0.1:8080");
  assert.equal(calls.length, 2);
});

test("a network failure on the default port still tries the alternate", async () => {
  let calls = 0;
  const base = await findDashboardApi(["http://localhost:8000", "http://127.0.0.1:8080"], {
    fetchImpl: async () => { if (++calls === 1) throw new TypeError("Failed to fetch"); return reply(200, dashboard); },
  });
  assert.equal(base, "http://127.0.0.1:8080");
});

test("a valid default backend is kept without probing another run", async () => {
  let calls = 0;
  const base = await findDashboardApi(dashboardApiCandidates("file:"), {
    fetchImpl: async () => { calls++; return reply(200, dashboard); },
  });
  assert.equal(base, "http://localhost:8000");
  assert.equal(calls, 1);
});

test("HTTP 200 from another application is not mistaken for mission data", async () => {
  for (const unrelated of [{ status: "ok" }, null, { ...dashboard, link: "yes" }]) {
    let calls = 0;
    const base = await findDashboardApi(["wrong", "remnant"], {
      fetchImpl: async () => reply(200, ++calls === 1 ? unrelated : dashboard),
    });
    assert.equal(base, "remnant");
  }
});

test("HTML responses are skipped and a hung probe is aborted", async () => {
  const base = await findDashboardApi(["html", "hung", "remnant"], {
    timeoutMs: 10,
    fetchImpl: async (url, { signal }) => {
      if (url.startsWith("html")) return { ok: true, json: async () => { throw new SyntaxError("HTML"); } };
      if (url.startsWith("hung")) return new Promise((_resolve, reject) => {
        signal.addEventListener("abort", () => reject(new Error("aborted")));
      });
      return reply(200, dashboard);
    },
  });
  assert.equal(base, "remnant");
});

test("no backend produces an actionable error instead of invented readings", async () => {
  await assert.rejects(findDashboardApi(["http://localhost:8000"], {
    fetchImpl: async () => reply(404),
  }), /Start the Remnant backend.*localhost:8000/);
});
