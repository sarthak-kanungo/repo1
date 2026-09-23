import { after, before, test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createApp } from "../src/app.js";

let server;
let baseUrl;
let tmpDir;

before(async () => {
  tmpDir = mkdtempSync(join(tmpdir(), "repo1-test-"));
  const app = createApp({ dataFile: join(tmpDir, "tasks.json") });
  await new Promise((resolve) => {
    server = app.listen(0, "127.0.0.1", resolve);
  });
  const { port } = server.address();
  baseUrl = `http://127.0.0.1:${port}`;
});

after(() => {
  server?.close();
  if (tmpDir) rmSync(tmpDir, { recursive: true, force: true });
});

test("health endpoint reports ok", async () => {
  const res = await fetch(`${baseUrl}/api/health`);
  assert.equal(res.status, 200);
  const body = await res.json();
  assert.equal(body.status, "ok");
});

test("starts with an empty task list", async () => {
  const res = await fetch(`${baseUrl}/api/tasks`);
  assert.equal(res.status, 200);
  assert.deepEqual(await res.json(), []);
});

test("creates, toggles, and deletes a task end to end", async () => {
  const createRes = await fetch(`${baseUrl}/api/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: "  Write the environment  " }),
  });
  assert.equal(createRes.status, 201);
  const created = await createRes.json();
  assert.equal(created.title, "Write the environment");
  assert.equal(created.done, false);
  assert.ok(created.id);

  const listRes = await fetch(`${baseUrl}/api/tasks`);
  assert.equal((await listRes.json()).length, 1);

  const toggleRes = await fetch(`${baseUrl}/api/tasks/${created.id}`, { method: "PATCH" });
  assert.equal(toggleRes.status, 200);
  assert.equal((await toggleRes.json()).done, true);

  const delRes = await fetch(`${baseUrl}/api/tasks/${created.id}`, { method: "DELETE" });
  assert.equal(delRes.status, 204);

  const finalRes = await fetch(`${baseUrl}/api/tasks`);
  assert.deepEqual(await finalRes.json(), []);
});

test("rejects a task without a title", async () => {
  const res = await fetch(`${baseUrl}/api/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: "   " }),
  });
  assert.equal(res.status, 400);
  assert.equal((await res.json()).error, "title is required");
});

test("returns 404 when toggling a missing task", async () => {
  const res = await fetch(`${baseUrl}/api/tasks/does-not-exist`, { method: "PATCH" });
  assert.equal(res.status, 404);
});
