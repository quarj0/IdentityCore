import { TeamInviteForm } from "@/components/forms/invite-team-form"; 
import { PageHeading } from "@/components/shared/page-heading";

export default function Page() {
  return (
    <div className="space-y-8">
      <PageHeading
        title="Invite team member"
        description="Invite teammates to collaborate on workflows, reviews, and administration."
      />
      <TeamInviteForm />
    </div>
  );
}
