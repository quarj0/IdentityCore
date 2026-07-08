import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Textarea,
} from "@identitycore/ui";

export function WebhookForm() {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardHeader>
        <CardTitle>Webhook endpoint</CardTitle>
      </CardHeader>

      <CardContent>
        <form className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="url">Endpoint URL</Label>
            <Input
              id="url"
              placeholder="https://app.example.com/webhooks/identitycore"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="events">Events</Label>
            <Textarea
              id="events"
              placeholder="workflow.session.completed, workflow.session.failed"
            />
          </div>

          <Button type="button" className="rounded-xl">
            Save webhook
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
