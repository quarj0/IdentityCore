import type { ReactNode } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";

interface DetailCardProps {
  title: string;
  children: ReactNode;
}

export function DetailCard({ title, children }: DetailCardProps) {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>

      <CardContent>{children}</CardContent>
    </Card>
  );
}
