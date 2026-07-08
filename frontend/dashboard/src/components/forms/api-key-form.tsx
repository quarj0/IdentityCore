import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Label,
} from "@identitycore/ui";

export function ApiKeyForm() {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardHeader>
        <CardTitle>Create API key</CardTitle>
      </CardHeader>

      <CardContent>
        <form className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="keyName">Key name</Label>
            <Input id="keyName" placeholder="Sandbox backend key" />
          </div>

          <div className="space-y-2">
            <Label htmlFor="environment">Environment</Label>
            <Input id="environment" placeholder="Sandbox" />
          </div>

          <Button type="button" className="rounded-xl">
            Create key
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
