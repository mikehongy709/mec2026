const { test } = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { join } = require("node:path");
const { Script } = require("node:vm");

test("the actual dashboard has no merge markers and its inline JavaScript parses", () => {
  const html = readFileSync(join(__dirname, "../index.html"), "utf8");
  assert.doesNotMatch(html, /^(?:<<<<<<<|=======|>>>>>>>)\s*.*$/m);
  const scripts = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)]
    .map(match => match[1]).filter(source => source.trim());
  assert.ok(scripts.length > 0, "Dashboard inline JavaScript must be checked");
  for (const source of scripts) {
    assert.doesNotThrow(() => new Script(source, { filename: "frontend/index.html" }));
  }
});
