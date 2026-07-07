import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Badge, Card, CardContent, CardHeader, CardTitle, PageHeader } from "@identitycore/ui";
import { getStatusBadgeVariant, verificationRequests, verificationSubjects } from "@/lib/mock-data";

export const metadata: Metadata = { title: "Subject Detail" };

export default async function VerificationSubjectDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const subject = verificationSubjects.find((item) => item.id === id);

  if (!subject) notFound();

  const subjectRequests = verificationRequests.filter((item) => item.subjectId === subject.id);

  return (
    <div className="space-y-6">
      <PageHeader
        title={subject.name}
        description={`Verification history and current status for ${subject.email}.`}
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Profile snapshot</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Status</span>
              <Badge variant={getStatusBadgeVariant(subject.status)}>{subject.status}</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Country</span>
              <span className="font-medium text-foreground">{subject.country}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Verifications</span>
              <span className="font-medium text-foreground">{subject.verifications}</span>
            </div>
            <div className="rounded-lg border border-border p-4">
              <div className="font-medium text-foreground">Notes</div>
              <p className="mt-2 leading-6 text-muted-foreground">{subject.notes}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Verification history</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {subjectRequests.map((request) => (
              <div key={request.id} className="rounded-lg border border-border p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="font-medium text-foreground">{request.id}</div>
                    <div className="text-sm text-muted-foreground">{request.policy}</div>
                  </div>
                  <Badge variant={getStatusBadgeVariant(request.status)}>{request.status}</Badge>
                </div>
                <div className="mt-3 text-sm text-muted-foreground">{request.decision}</div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
