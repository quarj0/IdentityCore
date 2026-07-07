import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";
import { AdminPageFrame } from "@/components/admin-page-frame";
import { tenants } from "@/lib/admin-data";

export const metadata: Metadata = { title: "Tenant Detail" };

export default async function PlatformAdminTenantDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const tenant = tenants.find((item) => item.id === id);

  if (!tenant) notFound();

  return (
    <AdminPageFrame
      title={tenant.name}
      description={`Tenant detail for ${tenant.region} operations and trust posture.`}
      actions={
        <>
          <Button variant="outline">Suspend tenant</Button>
          <Button>Approve changes</Button>
        </>
      }
    >
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <Card>
          <CardHeader><CardTitle className="text-base">Account state</CardTitle></CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="flex items-center justify-between"><span className="text-muted-foreground">Tier</span><span className="font-medium">{tenant.tier}</span></div>
            <div className="flex items-center justify-between"><span className="text-muted-foreground">Status</span><Badge variant={tenant.status === "Active" ? "success" : tenant.status === "Pending approval" ? "warning" : "destructive"}>{tenant.status}</Badge></div>
            <div className="flex items-center justify-between"><span className="text-muted-foreground">Verification volume</span><span className="font-medium">{tenant.verifications.toLocaleString()}</span></div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-base">Operational controls</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <div className="rounded-lg border border-border p-4">Tier changes should be paired with billing and review-queue checks.</div>
            <div className="rounded-lg border border-border p-4">Suspensions must document the abuse or compliance reason code.</div>
          </CardContent>
        </Card>
      </div>
    </AdminPageFrame>
  );
}
