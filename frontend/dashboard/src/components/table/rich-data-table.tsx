"use client";

import { useState } from "react";
import { ArrowDownUp, ChevronLeft, ChevronRight, Download } from "lucide-react";
import { Button, Checkbox } from "@identitycore/ui";
import { StatusBadge } from "@/components/shared/status-badge";

interface Column {
  key: string;
  label: string;
}

interface RichDataTableProps {
  columns: Column[];
  rows: Record<string, string>[];
}

export function RichDataTable({ columns, rows }: RichDataTableProps) {
  const [selected, setSelected] = useState<string[]>([]);

  const toggle = (id: string) => {
    setSelected((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id],
    );
  };

  return (
    <div className="space-y-4">
      {selected.length > 0 ? (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-3xl border border-blue-100 bg-blue-50 p-4">
          <p className="text-sm font-medium text-blue-700">
            {selected.length} selected
          </p>

          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="outline" className="rounded-xl bg-white">
              Export
            </Button>
            <Button size="sm" variant="outline" className="rounded-xl bg-white">
              Archive
            </Button>
            <Button size="sm" variant="destructive" className="rounded-xl">
              Delete
            </Button>
          </div>
        </div>
      ) : null}

      <div className="hidden overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm md:block">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-5 py-4">
                <span className="sr-only">Select</span>
              </th>
              {columns.map((column) => (
                <th key={column.key} className="px-5 py-4 font-medium">
                  <button className="inline-flex items-center gap-2">
                    {column.label}
                    <ArrowDownUp className="h-3.5 w-3.5" />
                  </button>
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-t border-slate-200">
                <td className="px-5 py-4">
                  <Checkbox
                    checked={selected.includes(row.id)}
                    onCheckedChange={() => toggle(row.id)}
                    aria-label={`Select ${row.name}`}
                  />
                </td>

                {columns.map((column) => (
                  <td key={column.key} className="px-5 py-4">
                    {column.key === "status" ? (
                      <StatusBadge status={row[column.key]} />
                    ) : (
                      <span className="text-slate-700">{row[column.key]}</span>
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid gap-3 md:hidden">
        {rows.map((row) => (
          <div
            key={row.id}
            className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-medium">{row.name}</p>
                <p className="mt-1 text-sm text-slate-500">{row.date}</p>
              </div>
              <StatusBadge status={row.status} />
            </div>
          </div>
        ))}
      </div>

      <div className="flex flex-col gap-3 rounded-3xl border border-slate-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between">
        <Button variant="outline" size="sm" className="rounded-xl">
          <Download className="h-4 w-4" />
          Export CSV
        </Button>

        <div className="flex items-center justify-end gap-2">
          <Button variant="outline" size="sm" className="rounded-xl">
            <ChevronLeft className="h-4 w-4" />
            Previous
          </Button>
          <span className="text-sm text-slate-500">Page 1 of 1</span>
          <Button variant="outline" size="sm" className="rounded-xl">
            Next
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
