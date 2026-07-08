import { FileText, Image, Video } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";

const evidence = [
  ["Document front", FileText],
  ["Document back", FileText],
  ["Selfie", Image],
  ["Liveness", Video],
];

export function EvidenceGallery() {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardHeader>
        <CardTitle>Evidence</CardTitle>
      </CardHeader>

      <CardContent className="grid gap-3 sm:grid-cols-2">
        {evidence.map(([label, Icon]) => {
          const LucideIcon = Icon as typeof FileText;

          return (
            <div
              key={label as string}
              className="rounded-2xl border border-slate-200 bg-slate-50 p-5"
            >
              <LucideIcon className="h-5 w-5 text-blue-600" />
              <p className="mt-4 text-sm font-medium">{label as string}</p>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}