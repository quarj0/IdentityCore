import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Label,
} from "@identitycore/ui";

export function TeamInviteForm() {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardHeader>
        <CardTitle>Invite team member</CardTitle>
      </CardHeader>

      <CardContent>
        <form className="grid gap-5 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="email">Email address</Label>
            <Input id="email" type="email" placeholder="member@company.com" />
          </div>

          <div className="space-y-2">
            <Label htmlFor="role">Role</Label>
            <Input id="role" placeholder="Reviewer" />
          </div>

          <div className="sm:col-span-2">
            <Button type="button" className="rounded-xl">
              Send invitation
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
