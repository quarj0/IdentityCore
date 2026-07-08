import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Textarea,
} from "@identitycore/ui";

export function ReviewWorkbench() {
  return (
    <div className="grid gap-6 xl:grid-cols-[0.65fr_0.35fr]">
      <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
        <CardHeader>
          <CardTitle>Evidence viewer</CardTitle>
        </CardHeader>

        <CardContent>
          <div className="flex min-h-96 items-center justify-center rounded-3xl bg-slate-950 text-white">
            Document / selfie comparison preview
          </div>
        </CardContent>
      </Card>

      <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
        <CardHeader>
          <CardTitle>Reviewer decision</CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          <Textarea placeholder="Add reviewer notes..." />

          <div className="grid gap-3">
            <Button className="rounded-xl">Approve</Button>
            <Button variant="outline" className="rounded-xl">
              Escalate
            </Button>
            <Button variant="destructive" className="rounded-xl">
              Reject
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
