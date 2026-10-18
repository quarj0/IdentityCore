export function csvCell(value: unknown) {
  const text = String(value ?? "");
  const safe =
    /^[\s]*[=+@-]/.test(text) || /^[\t\r\n]/.test(text) ? "'" + text : text;
  return `"${safe.replaceAll('"', '""')}"`;
}

export function downloadCsv(
  filename: string,
  rows: Array<Record<string, unknown>>,
) {
  const keys = Array.from(new Set(rows.flatMap((row) => Object.keys(row))));
  const csv = [
    keys.map(csvCell).join(","),
    ...rows.map((row) => keys.map((key) => csvCell(row[key])).join(",")),
  ].join("\n");
  const url = URL.createObjectURL(
    new Blob([csv], { type: "text/csv;charset=utf-8" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
