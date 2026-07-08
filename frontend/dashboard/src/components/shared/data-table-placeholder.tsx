import {
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@identitycore/ui";
import { StatusBadge } from "./status-badge";

interface DataTablePlaceholderProps {
  columns: { key: string; label: string }[];
  rows: Record<string, string>[];
}

export function DataTablePlaceholder({
  columns,
  rows,
}: DataTablePlaceholderProps) {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              {columns.map((column) => (
                <TableHead key={column.key} className="px-6 py-4">
                  {column.label}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>

          <TableBody>
            {rows.map((row, index) => (
              <TableRow key={index}>
                {columns.map((column) => {
                  const value = row[column.key] ?? "—";

                  return (
                    <TableCell key={column.key} className="px-6 py-4">
                      {column.key === "status" ? (
                        <StatusBadge status={value} />
                      ) : (
                        value
                      )}
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
