import { DocsLayout } from "@/components/docs/docs-layout";

const errors = [
  ["400", "bad_request", "The request payload is invalid."],
  ["401", "unauthorized", "Missing or invalid API key."],
  ["403", "forbidden", "The workspace cannot perform this action."],
  ["404", "not_found", "The requested resource does not exist."],
  ["409", "conflict", "The request conflicts with current state."],
  ["422", "validation_error", "One or more fields failed validation."],
  ["429", "rate_limited", "Too many requests."],
  ["500", "internal_error", "Unexpected server error."],
];

export default function ErrorsPage() {
  return (
    <DocsLayout
      title="Error codes"
      description="Common error responses returned by IdentityCore APIs."
    >
      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-5 py-4">Status</th>
              <th className="px-5 py-4">Code</th>
              <th className="px-5 py-4">Meaning</th>
            </tr>
          </thead>
          <tbody>
            {errors.map(([status, code, meaning]) => (
              <tr key={code} className="border-t border-slate-200">
                <td className="px-5 py-4 font-medium">{status}</td>
                <td className="px-5 py-4">
                  <code className="rounded bg-slate-100 px-2 py-1">{code}</code>
                </td>
                <td className="px-5 py-4 text-slate-600">{meaning}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </DocsLayout>
  );
}
