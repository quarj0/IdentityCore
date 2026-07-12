"use client";

import { useEffect, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import { PageHeader } from "@/components/shared/page-header";
import {
  buildComplianceConfig,
  compliancePolicyToRecord,
  fetchComplianceRecord,
} from "@/features/compliance/live-data";

type ComplianceDetailPageProps = {
  policyId: string;
};

export function ComplianceDetailPage({ policyId }: ComplianceDetailPageProps) {
  const [config, setConfig] = useState<ReturnType<typeof buildComplianceConfig> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setError(null);

      try {
        const policy = await fetchComplianceRecord(policyId);
        if (!active) return;
        if (!policy) {
          setError("Unable to load compliance policy.");
          return;
        }
        setConfig(buildComplianceConfig([compliancePolicyToRecord(policy)]));
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load compliance policy.",
          );
        }
      }
    }

    load();
    return () => {
      active = false;
    };
  }, [policyId]);

  if (error) {
    return (
      <EmptyState
        title="Unable to load compliance policy"
        description={error}
      />
    );
  }

  if (!config) {
    return (
      <div className="space-y-6 bg-white text-slate-950">
        <PageHeader
          eyebrow="Compliance"
          title="Loading compliance policy"
          description="Fetching the live policy from the backend."
        />
      </div>
    );
  }

  return <AdminDetailPage id={policyId} config={config} />;
}
