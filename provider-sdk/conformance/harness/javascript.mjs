// Synthetic stdin/stdout test driver; never expose these controls in production.
import { createInterface } from "node:readline";
import { mkdtempSync, readdirSync, readFileSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { inspect } from "node:util";
import { setTimeout } from "node:timers/promises";
import {
  ProviderRuntime,
  SQLiteStore,
  SigningKey,
} from "../../javascript/src/index.js";
let now = 1800000000;
const directory = mkdtempSync(join(tmpdir(), "identitycore-provider-harness-"));
const key = new SigningKey({
  keyId: "pec_synthetic",
  secret: "synthetic-wire-secret",
  tenantId: "ten_synthetic",
  environment: "sandbox",
  capabilities: ["document_ocr"],
});
const store = new SQLiteStore(join(directory, "provider.sqlite"), {
  encryptionKey: Buffer.from(Array.from({ length: 32 }, (_, i) => i)),
  clock: () => now,
});
const leases = new Map();
const runtime = new ProviderRuntime({
  keys: { [key.keyId]: key },
  store,
  handlers: {
    document_ocr: async (_id, inputs) => {
      await setTimeout(Math.min(inputs.delay_milliseconds ?? 0, 250));
      return {
        contract_version: "1",
        capability: "document_ocr",
        status: "completed",
        extracted_fields: { custom_attribute: "Private synthetic value" },
      };
    },
  },
  cancelHandler: () => true,
  deleteHandler: () => true,
});
try {
  for await (const line of createInterface({
    input: process.stdin,
    crlfDelay: Infinity,
  })) {
    let output;
    try {
      const command = JSON.parse(line);
      switch (command.action) {
        case "ping":
          output = { ready: true };
          break;
        case "handle": {
          const response = await runtime.handle({
            method: "POST",
            path: "/invoke",
            body: Buffer.from(command.body, "base64"),
            headers: command.headers,
            now,
          });
          output = {
            status: response.status,
            body: response.body.toString("base64"),
            headers: response.headers,
          };
          break;
        }
        case "claim": {
          const lease = await store.claimJob({ leaseSeconds: 30 });
          if (lease) leases.set(lease.operationId, lease);
          output = { claimed: !!lease };
          break;
        }
        case "complete":
          output = await store.complete(
            leases.get(command.operation_id),
            command.result,
          );
          break;
        case "callback": {
          const response = await runtime.callback(command.binding, {
            timestamp: now,
          });
          output = {
            body: response.body.toString("base64"),
            headers: response.headers,
          };
          break;
        }
        case "advance":
          now += command.seconds;
          output = { now };
          break;
        case "redaction":
          output = {
            safe:
              !inspect(key).includes(key.secret) &&
              readdirSync(directory).every(
                (name) =>
                  !readFileSync(join(directory, name)).includes(
                    "Private synthetic value",
                  ),
              ) &&
              [...leases.values()].every(
                (lease) =>
                  !inspect(lease).includes("Private synthetic value") &&
                  !inspect(lease).includes("synthetic-operation-lease-only"),
              ),
          };
          break;
        default:
          throw new Error();
      }
    } catch {
      output = { rejected: true };
    }
    process.stdout.write(JSON.stringify(output) + "\n");
  }
} finally {
  store.close();
  rmSync(directory, { recursive: true, force: true });
}
