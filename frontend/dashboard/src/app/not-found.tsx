import Link from "next/link";
import { SearchX } from "lucide-react";
import { Button, Card, CardContent } from "@identitycore/ui";

export default function NotFound() {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardContent className="flex min-h-96 flex-col items-center justify-center p-8 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
          <SearchX className="h-6 w-6" />
        </div>

        <h1 className="mt-6 text-2xl font-semibold">Page not found</h1>

        <p className="mt-2 max-w-md text-sm leading-7 text-slate-600">
          The dashboard page you are looking for does not exist.
        </p>

        <Button asChild className="mt-6 rounded-xl">
          <Link href="/">Back to overview</Link>
        </Button>
      </CardContent>
    </Card>
  );
}
