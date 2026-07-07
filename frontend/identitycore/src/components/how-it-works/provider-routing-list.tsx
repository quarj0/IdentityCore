const routes = [
  ["OCR", "IdentityCore OCR → Government OCR → Google Vision"],
  ["Face", "InsightFace → Internal Face AI → National DB"],
  ["Risk", "Rules Engine → Watchlists → Custom Signals"],
  ["Events", "Webhook → Dashboard → Review Queue"],
];

export function ProviderRoutingList() {
  return (
    <div className="grid gap-3">
      {routes.map(([title, value]) => (
        <div
          key={title}
          className="rounded-2xl border border-white/10 bg-white/[0.04] p-5"
        >
          <p className="text-xs font-medium uppercase tracking-wide text-blue-300">
            {title}
          </p>
          <p className="mt-2 text-sm text-slate-200">{value}</p>
        </div>
      ))}
    </div>
  );
}
