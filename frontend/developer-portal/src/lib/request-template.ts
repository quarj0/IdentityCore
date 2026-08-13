export function requiredHeadersTemplate(headers: string[] = []) {
  return headers
    .map((name) => {
      const variable = name.replace(/[^A-Za-z0-9]+/g, "_").toUpperCase();
      return ` \\
  -H "${name}: $IDENTITYCORE_${variable}"`;
    })
    .join("");
}
