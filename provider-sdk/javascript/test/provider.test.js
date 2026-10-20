import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { inspect } from "node:util";
import { spawn } from "node:child_process";
import {
  OPERATION_CONTRACT,
  ProviderRuntime,
  ProtocolError,
  SigningKey,
  SQLiteStore,
  jsonBytes,
  sign,
  verify,
} from "../src/index.js";
const NOW = 1800000000;
const storageKey = Buffer.from(Array.from({ length: 32 }, (_, i) => i));
function setup(t) {
  const directory = mkdtempSync(join(tmpdir(), "identitycore-provider-")),
    path = join(directory, "provider.sqlite");
  const store = new SQLiteStore(path, {
    encryptionKey: storageKey,
    clock: () => NOW,
  });
  t.after(() => {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  });
  const key = new SigningKey({
    keyId: "pec_synthetic",
    secret: "synthetic-wire-secret",
    tenantId: "ten_synthetic",
    environment: "sandbox",
    capabilities: ["document_ocr"],
  });
  const processed = [];
  const runtime = new ProviderRuntime({
    keys: { [key.keyId]: key },
    store,
    handlers: {
      document_ocr: async (id, inputs) => {
        processed.push(id);
        return {
          contract_version: "1",
          capability: "document_ocr",
          status: "completed",
          extracted_fields: { custom_attribute: inputs.custom_attribute },
        };
      },
    },
    cancelHandler: async () => true,
    deleteHandler: async () => true,
  });
  const binding = {
    operation_contract: OPERATION_CONTRACT,
    operation_id: "pop_synthetic",
    configuration_id: key.keyId,
    tenant_id: key.tenantId,
    project_id: "prj_synthetic",
    environment: "sandbox",
    capability: "document_ocr",
    contract_version: "1",
    request_sha256: "0".repeat(64),
    lease_generation: 1,
    deadline: new Date((NOW + 900) * 1000).toISOString(),
    callback_path: "/api/v1/providers/operations/pop_synthetic/callback",
    lease_token: "synthetic-operation-lease-only",
  };
  const request = async (payload, nonce) => {
    const body = jsonBytes(payload),
      headers = sign({
        method: "POST",
        path: "/invoke",
        body,
        key,
        timestamp: NOW,
        nonce,
      }),
      response = await runtime.handle({
        method: "POST",
        path: "/invoke",
        body,
        headers,
        now: NOW,
      });
    return { response, payload: JSON.parse(response.body) };
  };
  return { path, store, key, runtime, binding, request, processed };
}
test("published exact-wire fixture including non-ASCII bytes", async (t) => {
  const { store } = setup(t),
    fixture = JSON.parse(
      readFileSync(
        new URL(
          "../../../docs/fixtures/provider-signing-v1.json",
          import.meta.url,
        ),
      ),
    );
  const key = new SigningKey({
      keyId: fixture.key_id,
      secret: fixture.secret,
      tenantId: "ten_fixture",
      environment: "sandbox",
      capabilities: [],
    }),
    body = Buffer.from(fixture.canonical_body);
  const headers = sign({
    method: fixture.method,
    path: fixture.path,
    body,
    key,
    timestamp: fixture.timestamp,
    nonce: fixture.nonce,
  });
  assert.equal(headers["X-IC-Signature"], fixture.signature);
  await verify({
    method: fixture.method,
    path: fixture.path,
    body,
    headers,
    keys: { [key.keyId]: key },
    claimNonce: (hash, expires) => store.claimNonce(hash, expires),
    now: fixture.timestamp,
  });
  await assert.rejects(
    verify({
      method: fixture.method,
      path: fixture.path,
      body: Buffer.concat([body, Buffer.from(" ")]),
      headers,
      keys: { [key.keyId]: key },
      claimNonce: () => true,
      now: fixture.timestamp,
    }),
    ProtocolError,
  );
});
test("durable admission, one worker, encrypted values and signed callback", async (t) => {
  const { path, store, key, runtime, binding, request, processed } = setup(t);
  const start = {
    contract_version: "1",
    operation: "start",
    binding,
    inputs: { custom_attribute: "Private synthetic value" },
  };
  assert.equal((await request(start)).payload.status, "pending");
  assert.equal((await request(start)).payload.status, "pending");
  const result = await runtime.workOnce();
  assert.equal(
    result.result.extracted_fields.custom_attribute,
    "Private synthetic value",
  );
  assert.deepEqual(processed, ["pop_synthetic"]);
  assert.equal(await runtime.workOnce(), null);
  const callback = await runtime.callback(binding, { timestamp: NOW });
  assert.equal(JSON.parse(callback.body).status, "completed");
  await verify({
    method: "POST",
    path: binding.callback_path,
    ...callback,
    keys: { [key.keyId]: key },
    claimNonce: () => true,
    now: NOW,
  });
  assert.ok(
    !readFileSync(path).includes(Buffer.from("Private synthetic value")),
  );
  assert.ok(!readFileSync(path).includes(Buffer.from(binding.lease_token)));
  assert.equal(statSync(path).mode & 0o777, 0o600);
  assert.ok(!inspect(key).includes("synthetic-wire-secret"));
});
test("stale workers are fenced and cancel/delete prevent later completion", async (t) => {
  const { store, binding, request } = setup(t);
  await request({
    contract_version: "1",
    operation: "start",
    binding,
    inputs: { custom_attribute: "private" },
  });
  const lease = store.claimJob();
  assert.ok(!inspect(lease).includes("private"));
  assert.equal(store.claimJob(), null);
  store.clock = () => NOW + 31;
  const replacement = store.claimJob();
  assert.equal(replacement.generation, lease.generation + 1);
  const result = {
    contract_version: "1",
    capability: "document_ocr",
    status: "completed",
  };
  assert.throws(() => store.complete(lease, result), ProtocolError);
  assert.equal(
    (await request({ contract_version: "1", operation: "cancel", binding }))
      .payload.status,
    "cancelled",
  );
  assert.throws(() => store.complete(replacement, result), ProtocolError);
  assert.equal(
    (await request({ contract_version: "1", operation: "delete", binding }))
      .payload.status,
    "deleted",
  );
  assert.equal(
    (await request({ contract_version: "1", operation: "delete", binding }))
      .payload.status,
    "deleted",
  );
});
test("atomic replay across four independent Node processes", async (t) => {
  const { path } = setup(t),
    moduleUrl = new URL("../src/index.js", import.meta.url).href;
  const childEnv = { ...process.env };
  delete childEnv.NODE_TEST_CONTEXT;
  const run = () =>
    new Promise((resolve, reject) => {
      const child = spawn(
        process.execPath,
        [
          "--input-type=module",
          "-e",
          `import {SQLiteStore} from ${JSON.stringify(moduleUrl)};const store=new SQLiteStore(process.argv[1],{encryptionKey:Buffer.from(Array.from({length:32},(_,i)=>i)),clock:()=>${NOW}});process.stdout.write(String(store.claimNonce("shared-nonce",${NOW + 300})));store.close();`,
          path,
        ],
        { env: childEnv },
      );
      let output = "";
      child.stdout.on("data", (chunk) => (output += chunk));
      child.on("error", reject);
      child.on("close", (code) =>
        code === 0
          ? resolve(output.trim())
          : reject(new Error("Provider nonce subprocess failed")),
      );
    });
  assert.deepEqual((await Promise.all([run(), run(), run(), run()])).sort(), [
    "false",
    "false",
    "false",
    "true",
  ]);
});
test("wrong scope, malformed types, duplicate JSON and replay fail closed", async (t) => {
  const { runtime, binding, key, request } = setup(t);
  for (const [name, value] of [
    ["tenant_id", "ten_foreign"],
    ["environment", "production"],
    ["lease_generation", true],
    ["capability", []],
  ])
    assert.equal(
      (
        await request({
          contract_version: "1",
          operation: "start",
          binding: { ...binding, [name]: value },
          inputs: {},
        })
      ).response.status,
      400,
    );
  const body = Buffer.from('{"contract_version":"1","contract_version":"999"}'),
    headers = sign({
      method: "POST",
      path: "/invoke",
      body,
      key,
      timestamp: NOW,
    });
  assert.equal(
    (
      await runtime.handle({
        method: "POST",
        path: "/invoke",
        body,
        headers,
        now: NOW,
      })
    ).status,
    400,
  );
  const negotiation = {
    contract_version: "1",
    operation: "connection_test",
    environment: "sandbox",
    challenge: "synthetic",
    capabilities: ["document_ocr"],
    operation_contract: OPERATION_CONTRACT,
  };
  assert.equal(
    (await request(negotiation, "fixed-replay-nonce")).response.status,
    200,
  );
  assert.equal(
    (await request(negotiation, "fixed-replay-nonce")).response.status,
    403,
  );
});
