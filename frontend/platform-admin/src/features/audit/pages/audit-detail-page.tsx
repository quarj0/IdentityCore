"use client";

import { useEffect, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import { PageHeader } from "@/components/shared/page-header";
import { auditEventToRecord } from "@/features/audit/live-data";
import {
  buildAuditConfig,
  fetchAuditRecord,
} from "@/features/audit/live-data";

type AuditDetailPageProps = {
  auditId: string;
};

export function AuditDetailPage({ auditId }: AuditDetailPageProps) {
  const [config, setConfig] = useState<ReturnType<typeof buildAuditConfig> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setError(null);

      try {
        const record = await fetchAuditRecord(auditId);
        if (!active) return;
        if (!record) {
          setError("Unable to load audit event.");
          return;
        }
        setConfig(buildAuditConfig([auditEventToRecord(record)]));
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load audit event.",
          );
        }
      }
    }

    load();
    return () => {
      active = false;
    };
  }, [auditId]);

  if (error) {
    return (
      <EmptyState
        title="Unable to load audit event"
        description={error}
      />
    );
  }

  if (!config) {
    return (
      <div className="space-y-6 bg-white text-slate-950">
        <PageHeader
          eyebrow="Platform audit"
          title="Loading audit event"
          description="Fetching the live audit event from the backend."
        />
      </div>
    );
  }

  return <AdminDetailPage id={auditId} config={config} />;
}
