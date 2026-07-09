"use client";

import { useState } from "react";
import {
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@identitycore/ui";
import { UserPlus } from "lucide-react";

export function InviteAdminDialog() {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("");

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>
          <UserPlus className="mr-2 size-4" aria-hidden="true" />
          Invite admin
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Invite platform admin</DialogTitle>
          <DialogDescription>
            Invite an IdentityCore employee to the internal platform admin
            console.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="admin-email">Email address</Label>
            <Input
              id="admin-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="admin@identitycore.com"
            />
          </div>

          <div className="space-y-2">
            <Label>Role</Label>
            <Select value={role} onValueChange={setRole}>
              <SelectTrigger>
                <SelectValue placeholder="Select admin role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="platform-owner">Platform Owner</SelectItem>
                <SelectItem value="security-admin">Security Admin</SelectItem>
                <SelectItem value="compliance-admin">
                  Compliance Admin
                </SelectItem>
                <SelectItem value="support-lead">Support Lead</SelectItem>
                <SelectItem value="billing-admin">Billing Admin</SelectItem>
                <SelectItem value="read-only">Read Only</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button disabled={!email.trim() || !role}>Send invite</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
