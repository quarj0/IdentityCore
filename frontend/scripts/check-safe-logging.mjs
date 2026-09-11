import { readFileSync, readdirSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, extname, join, relative, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const frontendRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(import.meta.url);
const ts = require(
  resolve(
    frontendRoot,
    "packages/api-client/node_modules/typescript/lib/typescript.js",
  ),
);
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
const consoleMethods = new Set(["debug", "info", "log", "warn", "error", "trace"]);
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

function scriptKind(path) {
  if (path.endsWith(".tsx")) return ts.ScriptKind.TSX;
  if (path.endsWith(".jsx")) return ts.ScriptKind.JSX;
  if (path.endsWith(".ts")) return ts.ScriptKind.TS;
  return ts.ScriptKind.JS;
}

function propertyName(node) {
  if (ts.isIdentifier(node) || ts.isStringLiteralLike(node)) return node.text;
  return null;
}

function isConsoleObject(node) {
  if (ts.isIdentifier(node)) return node.text === "console";
  if (ts.isPropertyAccessExpression(node)) {
    return (
      ts.isIdentifier(node.expression) &&
      ["window", "globalThis"].includes(node.expression.text) &&
      node.name.text === "console"
    );
  }
  if (ts.isElementAccessExpression(node)) {
    return (
      ts.isIdentifier(node.expression) &&
      ["window", "globalThis"].includes(node.expression.text) &&
      propertyName(node.argumentExpression) === "console"
    );
  }
  return false;
}

function isConsoleMethodReference(node) {
  if (ts.isPropertyAccessExpression(node)) {
    return isConsoleObject(node.expression) && consoleMethods.has(node.name.text);
  }
  if (ts.isElementAccessExpression(node)) {
    const method = propertyName(node.argumentExpression);
    return isConsoleObject(node.expression) && method !== null && consoleMethods.has(method);
  }
  return false;
}

function destructuresConsoleMethod(node) {
  if (!ts.isVariableDeclaration(node) || !ts.isObjectBindingPattern(node.name)) return false;
  if (!node.initializer || !isConsoleObject(node.initializer)) return false;
  return node.name.elements.some((element) => {
    const name = propertyName(element.propertyName ?? element.name);
    return name !== null && consoleMethods.has(name);
  });
}

export function containsUnsafeConsoleUse(path, source) {
  const sourceFile = ts.createSourceFile(
    path,
    source,
    ts.ScriptTarget.Latest,
    true,
    scriptKind(path),
  );
  let found = false;

  function visit(node) {
    if (found) return;
    if (
      ((ts.isCallExpression(node) && isConsoleMethodReference(node.expression)) ||
        isConsoleMethodReference(node) ||
        destructuresConsoleMethod(node))
    ) {
      found = true;
      return;
    }
    ts.forEachChild(node, visit);
  }

  visit(sourceFile);
  return found;
}

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
    if (containsUnsafeConsoleUse(absolute, source)) {
      findings.push(relative(frontendRoot, absolute));
    }
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
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
}
