import { Download } from "lucide-react";
import { Button } from "@identitycore/ui";

export function ExportActions() {
  return (
    <div className="flex flex-wrap gap-2">
      <Button variant="outline" size="sm" className="rounded-xl">
        <Download className="h-4 w-4" />
        Export CSV
      </Button>
      <Button variant="outline" size="sm" className="rounded-xl">
        <Download className="h-4 w-4" />
        Export JSON
      </Button>
      <Button variant="outline" size="sm" className="rounded-xl">
        <Download className="h-4 w-4" />
        Export audit
      </Button>
    </div>
  );
}
