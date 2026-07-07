import type { Metadata } from "next";
import { Badge, Button, Card, CardContent, Avatar, AvatarFallback, PageHeader } from "@identitycore/ui";
import { Plus, UserPlus, Shield, MoreVertical } from "lucide-react";

export const metadata: Metadata = { title: "Team Management" };

const team = [
  { id: "member-1", name: "Alex Carter", email: "alex.c@acme.com", role: "Owner", status: "Active" },
  { id: "member-2", name: "Sarah Connor", email: "sarah.c@acme.com", role: "Developer", status: "Active" },
  { id: "member-3", name: "David Miller", email: "david.m@acme.com", role: "Verification Officer", status: "Active" },
  { id: "member-4", name: "Elena Rostova", email: "elena.r@acme.com", role: "Compliance Reviewer", status: "Invited" },
];

function initials(name: string) {
  return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
}

export default function TeamPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Team"
        description="Manage team members, roles, and permissions."
        actions={
          <Button id="invite-member">
            <UserPlus className="h-4 w-4" />
            Invite member
          </Button>
        }
      />

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Member</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Role</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Status</th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {team.map((member) => (
                <tr key={member.id} className="transition-colors hover:bg-muted/30">
                  <td className="px-6 py-3.5 flex items-center gap-3">
                    <Avatar className="h-8 w-8">
                      <AvatarFallback className="text-xs bg-muted text-muted-foreground">
                        {initials(member.name)}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="font-medium text-foreground">{member.name}</div>
                      <div className="text-xs text-muted-foreground">{member.email}</div>
                    </div>
                  </td>
                  <td className="px-6 py-3.5">
                    <span className="inline-flex items-center gap-1 text-xs text-foreground font-medium">
                      <Shield className="h-3 w-3 text-muted-foreground" />
                      {member.role}
                    </span>
                  </td>
                  <td className="px-6 py-3.5">
                    <Badge variant={member.status === "Active" ? "success" : "secondary"}>
                      {member.status}
                    </Badge>
                  </td>
                  <td className="px-6 py-3.5 text-right">
                    <Button variant="ghost" size="icon" className="h-8 w-8" id={`manage-member-${member.id}`}>
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
