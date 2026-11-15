const { test } = require("node:test");
const assert = require("node:assert/strict");
const { PacketClient } = require("../packet-client.js");

const packet = { alt: 0, vel: 0, g: 1, tmp: 24, pwr: 98, prs: 310, seq: 1, crc: 4421 };
const receipt = { id: 1, stream_id: "run-1", seq: 1, duplicate: false };
const reply = (status, body = receipt) => ({ status, json: async () => body });
const client = fetchImpl => new PacketClient({ streamId: "run-1", fetchImpl });

test("the browser fetch function retains its global receiver", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async function () {
    assert.equal(this, globalThis);
    return reply(201);
  };
  try {
    const validator = new PacketClient({ streamId: "run-1" });
    assert.equal((await validator.check(packet)).status, "accepted");
  } finally {
    globalThis.fetch = original;
  }
});

test("posts the unchanged packet to the selected backend and run", async () => {
  const validator = new PacketClient({
    apiBase: "http://localhost:8000/", streamId: "run-1",
    fetchImpl: async (url, options) => {
      assert.equal(url, "http://localhost:8000/api/packet-streams/run-1/packets");
      assert.equal(options.method, "POST");
      assert.equal(options.headers["Content-Type"], "application/json");
      assert.deepEqual(JSON.parse(options.body), packet);
      assert.ok(options.signal instanceof AbortSignal);
      return reply(201);
    },
  });
  assert.deepEqual(await validator.check(packet), { status: "accepted" });
});

test("a replay is delivered to charts only once", async () => {
  let calls = 0;
  const validator = client(async () => ++calls === 1 ? reply(201) : reply(200, { ...receipt, duplicate: true }));
  assert.equal((await validator.check(packet)).status, "accepted");
  assert.equal((await validator.check(packet)).status, "duplicate");
  assert.equal(calls, 2);
});

test("validation errors and sequence conflicts never deliver readings", async () => {
  for (const code of [409, 422]) {
    const validator = client(async () => reply(code));
    assert.equal((await validator.check(packet)).status, "rejected");
    assert.equal(validator.delivered.size, 0);
  }
});

test("a changed packet reusing a delivered sequence still goes to backend checks", async () => {
  let calls = 0;
  const validator = client(async () => ++calls === 1 ? reply(201) : reply(409));
  assert.equal((await validator.check(packet)).status, "accepted");
  assert.equal((await validator.check({ ...packet, tmp: 25 })).status, "rejected");
  assert.equal(calls, 2);
});

test("lost API response retries the original payload and delivers a server duplicate once", async () => {
  const bodies = [];
  const validator = client(async (_url, options) => {
    bodies.push(options.body);
    if (bodies.length === 1) throw new TypeError("Failed to fetch");
    return reply(200, { ...receipt, duplicate: true });
  });
  assert.equal((await validator.check(packet)).status, "unavailable");
  assert.equal((await validator.check(packet)).status, "accepted");
  assert.equal((await validator.check(packet)).status, "duplicate");
  assert.equal(new Set(bodies).size, 1);
});

test("API errors do not mark a packet delivered or rejected", async () => {
  for (const code of [404, 500, 503]) {
    let calls = 0;
    const validator = client(async () => ++calls === 1 ? reply(code) : reply(201));
    assert.equal((await validator.check(packet)).status, "unavailable");
    assert.equal((await validator.check(packet)).status, "accepted");
  }
});

test("malformed receipts cannot authorize a chart update", async () => {
  for (const body of [null, {}, { ...receipt, stream_id: "other" }, { ...receipt, seq: 2 },
    { ...receipt, id: 0 }, { ...receipt, duplicate: "false" }]) {
    const validator = client(async () => reply(201, body));
    assert.equal((await validator.check(packet)).status, "unavailable");
    assert.equal(validator.delivered.size, 0);
  }
});

test("non-JSON receipts are treated as unavailable and remain retryable", async () => {
  const validator = client(async () => ({ status: 201, json: async () => { throw new SyntaxError("not JSON"); } }));
  assert.equal((await validator.check(packet)).status, "unavailable");
  assert.equal(validator.delivered.size, 0);
});

test("a hung request is aborted without delivering a packet", async () => {
  const validator = new PacketClient({
    streamId: "run-1", timeoutMs: 10,
    fetchImpl: (_url, { signal }) => new Promise((_resolve, reject) => {
      signal.addEventListener("abort", () => reject(Object.assign(new Error("aborted"), { name: "AbortError" })));
    }),
  });
  assert.deepEqual(await validator.check(packet), { status: "unavailable", message: "Packet API timed out" });
  assert.equal(validator.delivered.size, 0);
});

test("a new run can start its sequence at one", async () => {
  for (const streamId of ["run-1", "run-2"]) {
    const validator = new PacketClient({ streamId, fetchImpl: async () => reply(201, { ...receipt, stream_id: streamId }) });
    assert.equal((await validator.check(packet)).status, "accepted");
  }
});

test("out-of-order unique sequences are accepted", async () => {
  const validator = client(async (_url, options) => reply(201, { ...receipt, seq: JSON.parse(options.body).seq }));
  assert.equal((await validator.check({ ...packet, seq: 10 })).status, "accepted");
  assert.equal((await validator.check(packet)).status, "accepted");
});
