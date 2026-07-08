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

export function ProjectForm() {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardHeader>
        <CardTitle>Project details</CardTitle>
      </CardHeader>

      <CardContent>
        <form className="grid gap-5 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="projectName">Project name</Label>
            <Input id="projectName" placeholder="Default Sandbox" />
          </div>

          <div className="space-y-2">
            <Label htmlFor="environment">Environment</Label>
            <Input id="environment" placeholder="Sandbox" />
          </div>

          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Describe what this project is used for."
            />
          </div>

          <div className="sm:col-span-2">
            <Button type="button" className="rounded-xl">
              Save project
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
