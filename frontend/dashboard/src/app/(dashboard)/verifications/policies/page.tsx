import type { Metadata } from "next";
import { Plus, Settings, Shield, Eye, ToggleRight } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Badge,
  PageHeader,
  Button,
} from "@identitycore/ui";

export const metadata: Metadata = { title: "Verification Policies" };

const policies = [
  {
    id: "pol-standard-kyc",
    name: "Standard KYC",
    description: "Government ID + selfie with face match",
    docTypes: ["Passport", "National ID", "Driver's License"],
    selfie: true,
    liveness: false,
    faceMatchThreshold: 80,
    manualReviewThreshold: 70,
    expiryDays: 7,
    active: true,
    usageCount: 8420,
  },
  {
    id: "pol-enhanced-kyc",
    name: "Enhanced KYC",
    description: "Passport only with selfie + liveness check",
    docTypes: ["Passport"],
    selfie: true,
    liveness: true,
    faceMatchThreshold: 90,
    manualReviewThreshold: 80,
    expiryDays: 7,
    active: true,
    usageCount: 3211,
  },
  {
    id: "pol-lite-kyc",
    name: "Lite KYC",
    description: "Any government ID, no selfie required",
    docTypes: ["Passport", "National ID", "Driver's License"],
    selfie: false,
    liveness: false,
    faceMatchThreshold: null,
    manualReviewThreshold: 60,
    expiryDays: 14,
    active: false,
    usageCount: 1216,
  },
];

export default function PoliciesPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Verification policies"
        description="Configure documents and checks required for each verification flow."
        actions={
          <Button id="create-policy">
            <Plus className="h-4 w-4" />
            New policy
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {policies.map((policy) => (
          <Card key={policy.id} id={`policy-card-${policy.id}`} className="flex flex-col">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/8">
                    <Shield className="h-4 w-4 text-primary" strokeWidth={1.75} />
                  </div>
                  <div>
                    <CardTitle className="text-sm">{policy.name}</CardTitle>
                    <div className="mt-0.5 text-xs text-muted-foreground">
                      {policy.usageCount.toLocaleString()} uses
                    </div>
                  </div>
                </div>
                <Badge variant={policy.active ? "success" : "secondary"}>
                  {policy.active ? "Active" : "Inactive"}
                </Badge>
              </div>
              <CardDescription className="mt-2 text-xs">{policy.description}</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col flex-1 gap-3 pt-0">
              {/* Document types */}
              <div>
                <div className="mb-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Accepted Documents
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {policy.docTypes.map((d) => (
                    <Badge key={d} variant="outline" className="text-xs font-normal">
                      {d}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Checks */}
              <div className="grid grid-cols-2 gap-1.5 text-xs">
                <div className={`flex items-center gap-1.5 ${policy.selfie ? "text-foreground" : "text-muted-foreground/50 line-through"}`}>
                  <ToggleRight className="h-3.5 w-3.5" />
                  Selfie required
                </div>
                <div className={`flex items-center gap-1.5 ${policy.liveness ? "text-foreground" : "text-muted-foreground/50 line-through"}`}>
                  <ToggleRight className="h-3.5 w-3.5" />
                  Liveness check
                </div>
              </div>

              {/* Thresholds */}
              {policy.faceMatchThreshold && (
                <div className="rounded-md bg-muted/50 px-3 py-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Face match threshold</span>
                    <span className="font-medium">{policy.faceMatchThreshold}%</span>
                  </div>
                  <div className="mt-1 flex justify-between">
                    <span className="text-muted-foreground">Manual review threshold</span>
                    <span className="font-medium">{policy.manualReviewThreshold}%</span>
                  </div>
                  <div className="mt-1 flex justify-between">
                    <span className="text-muted-foreground">Link expiry</span>
                    <span className="font-medium">{policy.expiryDays} days</span>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="mt-auto flex gap-2 pt-2">
                <Button variant="outline" size="sm" className="flex-1 h-8 gap-1.5" id={`view-policy-${policy.id}`}>
                  <Eye className="h-3.5 w-3.5" />
                  View
                </Button>
                <Button variant="outline" size="sm" className="flex-1 h-8 gap-1.5" id={`edit-policy-${policy.id}`}>
                  <Settings className="h-3.5 w-3.5" />
                  Edit
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
