import { readFileSync, readdirSync } from "node:fs";
import { dirname, extname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontendRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const allowedConsoleFile = resolve(
  frontendRoot,
  "packages/api-client/src/safe-logging.ts",
);
const sourceRoots = [
  "dashboard",
  "developer-portal",
  "identitycore",
  "platform-admin",
  "verification-portal",
  "packages",
].map((path) => resolve(frontendRoot, path));
const extensions = new Set([".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"]);
const directConsole = /\bconsole\.(?:debug|info|log|warn|error|trace)\s*\(/;
const skipDirectories = new Set([
  ".next",
  ".safe-logging-test",
  "coverage",
  "dist",
  "e2e",
  "node_modules",
  "test",
  "tests",
]);

function walk(path, findings) {
  for (const entry of readdirSync(path, { withFileTypes: true })) {
    if (entry.isDirectory() && skipDirectories.has(entry.name)) continue;
    const absolute = join(path, entry.name);
    if (entry.isDirectory()) {
      walk(absolute, findings);
      continue;
    }
    if (!extensions.has(extname(entry.name))) continue;
    if (/\.(?:spec|test)\.[cm]?[jt]sx?$/.test(entry.name)) continue;
    if (absolute === allowedConsoleFile) continue;
    const source = readFileSync(absolute, "utf8");
    if (directConsole.test(source)) findings.push(relative(frontendRoot, absolute));
  }
}

const findings = [];
for (const root of sourceRoots) walk(root, findings);

if (findings.length) {
  console.error(
    [
      "Unsafe direct console logging is not allowed in frontend production source.",
      "Use safeLog from @identitycore/api-client so sensitive context is redacted.",
      ...findings.map((path) => ` - ${path}`),
    ].join("\n"),
  );
  process.exitCode = 1;
}
