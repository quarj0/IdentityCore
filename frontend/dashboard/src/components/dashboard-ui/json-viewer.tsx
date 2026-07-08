interface JsonViewerProps {
  value: unknown;
}

export function JsonViewer({ value }: JsonViewerProps) {
  return (
    <pre className="overflow-x-auto rounded-2xl bg-slate-950 p-5 text-sm leading-7 text-slate-200">
      <code>{JSON.stringify(value, null, 2)}</code>
    </pre>
  );
}
