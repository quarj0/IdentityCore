const assert = require("node:assert/strict");
const { createRequire } = require("node:module");
const path = require("node:path");
const test = require("node:test");
const { spawnSync } = require("node:child_process");

// Exercise the copies actually consumed by ESLint and Swagger UI.
function dependencyPath(names) {
  let requireDependency = createRequire(
    path.join(__dirname, "../developer-portal/package.json"),
  );
  let resolved;
  for (const name of names) {
    resolved = requireDependency.resolve(name);
    requireDependency = createRequire(resolved);
  }
  return resolved;
}

function dependencyChain(names) {
  return require(dependencyPath(names));
}

const braces = dependencyChain([
  "eslint-config-next",
  "@next/eslint-plugin-next",
  "fast-glob",
  "micromatch",
  "braces",
]);
const { sprintf } = dependencyChain([
  "swagger-ui-react",
  "remarkable",
  "argparse",
  "sprintf-js",
]);

test("deep patterns remain safe with limited available JavaScript stack", () => {
  const bracesPath = dependencyPath([
    "eslint-config-next",
    "@next/eslint-plugin-next",
    "fast-glob",
    "micromatch",
    "braces",
  ]);
  const script = `const braces = require(${JSON.stringify(bracesPath)});
    const input = '{'.repeat(4000) + 'a,b' + '}'.repeat(4000);
    for (const method of ['compile', 'expand', 'stringify']) braces[method](input);`;
  const result = spawnSync(
    process.execPath,
    ["--stack-size=256", "-e", script],
    {
      encoding: "utf8",
      timeout: 5000,
    },
  );
  assert.equal(result.status, 0, result.stderr || String(result.error));
});

test("deep brace and parenthesis patterns remain literal through every parsed-string API", () => {
  for (const [open, close] of [
    ["{", "}"],
    ["(", ")"],
  ]) {
    for (const matched of [true, false]) {
      const input =
        open.repeat(4000) + "a,b" + (matched ? close.repeat(4000) : "");
      const ast = braces.parse(input);
      assert.equal(braces.stringify(ast), input);
      assert.equal(braces.stringify(input), input);
      assert.deepEqual(braces.expand(input), [input]);
      assert.deepEqual(braces.expand(ast), [input]);
      assert.deepEqual(braces(input, { expand: true }), [input]);
      for (const compiled of [
        braces.compile(input),
        braces.compile(ast),
        ...braces(input),
      ]) {
        const regex = new RegExp("^(?:" + compiled + ")$");
        assert.ok(regex.test(input));
        assert.equal(regex.test("a"), false);
      }
    }
  }
});

test("normal brace alternatives and ranges retain their behavior", () => {
  assert.deepEqual(braces.expand("file-{a,b}-{1..2}"), [
    "file-a-1",
    "file-a-2",
    "file-b-1",
    "file-b-2",
  ]);
  assert.ok(new RegExp("^" + braces.compile("{a,b}") + "$").test("b"));
  assert.equal(braces.stringify(braces.parse("file-{a,b}")), "file-{a,b}");
});

test("numeric precision cannot trigger native RangeError", () => {
  for (const conversion of ["e", "f", "g"]) {
    for (const precision of ["101", "1000000", "9".repeat(400)]) {
      const result = sprintf("%." + precision + conversion, 1.25);
      assert.equal(result, sprintf("%.100" + conversion, 1.25));
      assert.ok(result.length < 110);
    }
  }
  assert.equal(sprintf("%.0g", 1.25), sprintf("%.1g", 1.25));
});

test("ordinary Swagger/argparse formatting remains compatible", () => {
  assert.equal(sprintf("%s: %.2f", "value", 1.25), "value: 1.25");
  assert.equal(sprintf("%04d", 12), "0012");
  assert.equal(sprintf("%.2e", 1.25), "1.25e+0");
  assert.equal(sprintf("%.3g", 1.25), "1.25");
});
