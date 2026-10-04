"use client";
import { useEffect, useState } from "react";
import {
  Button,
  Card,
  CardContent,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@identitycore/ui";
import { PageHeading } from "@/components/shared/page-heading";
import { dashboardApi } from "@/lib/dashboard-api";
export function LiveInvitationsPage() {
  const [items, setItems] = useState<Array<Record<string, unknown>>>([]),
    [roles, setRoles] = useState<Array<{ id: string; name: string }>>([]),
    [email, setEmail] = useState(""),
    [role, setRole] = useState(""),
    [message, setMessage] = useState("");
  const load = () =>
    dashboardApi.invitations().then((x) => setItems(x.results));
  useEffect(() => {
    load().catch(() =>
      setMessage(
        "Invitations could not be loaded. Organization management access is required.",
      ),
    );
    dashboardApi
      .roles()
      .then((x) => {
        setRoles(x.results);
        setRole(x.results[0]?.id ?? "");
      })
      .catch(() => setMessage("Roles could not be loaded."));
  }, []);
  async function invite() {
    try {
      setMessage("");
      await dashboardApi.createInvitation({ email, role_id: role });
      setEmail("");
      await load();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Invitation failed.");
    }
  }
  async function change(id: string, action: "resend" | "revoke") {
    try {
      setMessage("");
      await dashboardApi.invitationAction(id, action);
      await load();
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Invitation action failed.",
      );
    }
  }
  return (
    <div className="space-y-8">
      <PageHeading
        title="Team invitations"
        description="Invite tenant members into an existing role."
      />
      <Card>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void invite();
          }}
        >
          <CardContent className="grid gap-3 p-6 md:grid-cols-[1fr_220px_auto]">
            <Input
              type="email"
              required
              aria-label="Recipient email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="person@company.com"
            />
            <Select value={role} onValueChange={setRole}>
              <SelectTrigger>
                <SelectValue placeholder="Role" />
              </SelectTrigger>
              <SelectContent>
                {roles.map((x) => (
                  <SelectItem value={x.id} key={x.id}>
                    {x.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button type="submit" disabled={!email || !role}>
              Send invitation
            </Button>
          </CardContent>
        </form>
      </Card>
      {message ? <p className="text-sm text-red-700">{message}</p> : null}
      <div className="space-y-3">
        {items.map((x) => (
          <Card key={String(x.id)}>
            <CardContent className="flex justify-between p-5">
              <span>{String(x.email)}</span>
              <span className="capitalize text-slate-500">
                {String(x.role)} · {String(x.status)}
              </span>
              {(x.status === "pending" || x.status === "expired") && (
                <div className="flex gap-2">
                  <Button onClick={() => void change(String(x.id), "resend")}>
                    Resend
                  </Button>
                  <Button onClick={() => void change(String(x.id), "revoke")}>
                    Revoke
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
