import Link from "next/link";
import { Button } from "@identitycore/ui";
import type { GlobalTemplate } from "@/features/templates/mock-data";
import { TemplateStatusPill } from "@/features/templates/components/template-status-pill";

type TemplatesTableProps = {
  templates: GlobalTemplate[];
};

export function TemplatesTable({ templates }: TemplatesTableProps) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1050px] text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th scope="col" className="px-5 py-4 font-medium">Template</th>
              <th scope="col" className="px-5 py-4 font-medium">Status</th>
              <th scope="col" className="px-5 py-4 font-medium">Category</th>
              <th scope="col" className="px-5 py-4 font-medium">Version</th>
              <th scope="col" className="px-5 py-4 font-medium">Countries</th>
              <th scope="col" className="px-5 py-4 font-medium">Usage</th>
              <th scope="col" className="px-5 py-4 font-medium">Risk</th>
              <th scope="col" className="px-5 py-4 text-right font-medium">Actions</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200">
            {templates.map((template) => (
              <tr key={template.id} className="transition hover:bg-slate-50">
                <td className="px-5 py-4">
                  <Link
                    href={`/templates/${template.id}`}
                    className="font-medium text-slate-950 outline-none hover:text-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500"
                  >
                    {template.name}
                  </Link>
                  <p className="mt-1 max-w-md text-xs text-slate-500">
                    {template.description}
                  </p>
                </td>

                <td className="px-5 py-4">
                  <TemplateStatusPill status={template.status} />
                </td>

                <td className="px-5 py-4 text-slate-700">{template.category}</td>
                <td className="px-5 py-4 text-slate-700">{template.version}</td>
                <td className="px-5 py-4 text-slate-700">
                  {template.countries.join(", ")}
                </td>
                <td className="px-5 py-4 text-slate-700">
                  {template.usageCount.toLocaleString()}
                </td>
                <td className="px-5 py-4 text-slate-700">{template.riskLevel}</td>

                <td className="px-5 py-4 text-right">
                  <Button asChild variant="outline" size="sm">
                    <Link href={`/templates/${template.id}`}>View</Link>
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}