import Link from "next/link";
import { Button } from "@identitycore/ui";
import type { GlobalWorkflow } from "@/features/workflows/mock-data";
import { WorkflowStatusPill } from "@/features/workflows/components/workflow-status-pill";

type WorkflowsTableProps = {
  workflows: GlobalWorkflow[];
};

export function WorkflowsTable({ workflows }: WorkflowsTableProps) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1100px] text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th scope="col" className="px-5 py-4 font-medium">Workflow</th>
              <th scope="col" className="px-5 py-4 font-medium">Status</th>
              <th scope="col" className="px-5 py-4 font-medium">Category</th>
              <th scope="col" className="px-5 py-4 font-medium">Version</th>
              <th scope="col" className="px-5 py-4 font-medium">Countries</th>
              <th scope="col" className="px-5 py-4 font-medium">Organizations</th>
              <th scope="col" className="px-5 py-4 font-medium">Monthly runs</th>
              <th scope="col" className="px-5 py-4 text-right font-medium">Actions</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200">
            {workflows.map((workflow) => (
              <tr key={workflow.id} className="transition hover:bg-slate-50">
                <td className="px-5 py-4">
                  <Link
                    href={`/workflows/${workflow.id}`}
                    className="font-medium text-slate-950 outline-none hover:text-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500"
                  >
                    {workflow.name}
                  </Link>
                  <p className="mt-1 max-w-md text-xs text-slate-500">
                    {workflow.description}
                  </p>
                </td>

                <td className="px-5 py-4">
                  <WorkflowStatusPill status={workflow.status} />
                </td>

                <td className="px-5 py-4 text-slate-700">{workflow.category}</td>
                <td className="px-5 py-4 text-slate-700">{workflow.version}</td>
                <td className="px-5 py-4 text-slate-700">
                  {workflow.countries.join(", ")}
                </td>
                <td className="px-5 py-4 text-slate-700">
                  {workflow.organizationsUsing}
                </td>
                <td className="px-5 py-4 text-slate-700">
                  {workflow.monthlyRuns.toLocaleString()}
                </td>

                <td className="px-5 py-4 text-right">
                  <Button asChild variant="outline" size="sm">
                    <Link href={`/workflows/${workflow.id}`}>View</Link>
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