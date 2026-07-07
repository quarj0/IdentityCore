const providerTypes = [
  "IdentityCore OCR",
  "Custom OCR",
  "Government ID API",
  "Face AI",
  "Liveness Provider",
  "Risk Engine",
  "Watchlist Provider",
  "Internal Database",
];

export function ProviderGrid() {
  return (
    <div className="rounded-[2rem] border border-white/10 bg-white/[0.03] p-5">
      <div className="grid gap-3 sm:grid-cols-2">
        {providerTypes.map((provider) => (
          <div
            key={provider}
            className="rounded-2xl border border-white/10 bg-white/[0.04] p-4"
          >
            <p className="text-sm font-medium">{provider}</p>
            <p className="mt-1 text-xs text-slate-400">
              Connect through provider adapters
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
