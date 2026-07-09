import {
  Activity,
  AlertTriangle,
  BarChart3,
  Building2,
  CheckCircle2,
  CreditCard,
  Network,
  UserCheck,
} from "lucide-react";
import { MetricCard } from "@/components/shared/metric-card";
import { dashboardMetrics } from "@/features/dashboard/mock-data";

const icons = [
  Building2,
  UserCheck,
  Network,
  CheckCircle2,
  Activity,
  AlertTriangle,
  CreditCard,
  BarChart3,
];

export function DashboardMetricsGrid() {
  return (
    <section
      className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
      aria-label="Platform metrics"
    >
      {dashboardMetrics.map((metric, index) => (
        <MetricCard
          key={metric.label}
          label={metric.label}
          value={metric.value}
          change={metric.change}
          trend={metric.trend}
          helperText={metric.helperText}
          icon={icons[index]}
        />
      ))}
    </section>
  );
}
