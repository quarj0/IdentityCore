import { AlertTriangle } from "lucide-react";
import { Button, Card, CardContent } from "@identitycore/ui";

interface ConfirmationCardProps {
  title: string;
  description: string;
  actionLabel: string;
}

export function ConfirmationCard({
  title,
  description,
  actionLabel,
}: ConfirmationCardProps) {
  return (
    <Card className="rounded-3xl border-red-200 bg-red-50 shadow-sm">
      <CardContent className="flex flex-col gap-5 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex gap-3">
          <AlertTriangle className="mt-1 h-5 w-5 shrink-0 text-red-700" />
          <div>
            <h2 className="font-semibold text-red-950">{title}</h2>
            <p className="mt-1 text-sm leading-6 text-red-800">{description}</p>
          </div>
        </div>

        <Button variant="destructive" className="rounded-xl">
          {actionLabel}
        </Button>
      </CardContent>
    </Card>
  );
}
