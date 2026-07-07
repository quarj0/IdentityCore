import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { ArrowRight } from "lucide-react";
import { Card, CardDescription, CardHeader, CardTitle } from "@identitycore/ui";

interface SolutionCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
  useCases: string[];
  slug: string;
}

export function SolutionCard({
  title,
  description,
  icon: Icon,
  useCases,
  slug,
}: SolutionCardProps) {
  return (
    <Card className="group rounded-3xl border-slate-200 bg-white p-2 shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl">
      <CardHeader className="p-6">
        <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
          <Icon className="h-5 w-5" />
        </div>

        <CardTitle>{title}</CardTitle>
        <CardDescription className="pt-2 leading-7">
          {description}
        </CardDescription>

        <div className="flex flex-wrap gap-2 pt-5">
          {useCases.map((item) => (
            <span
              key={item}
              className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700"
            >
              {item}
            </span>
          ))}
        </div>

        <Link
          href={`/solutions/${slug}`}
          className="flex items-center gap-2 pt-6 text-sm font-medium text-blue-600 hover:text-blue-700"
        >
          Explore solution
          <ArrowRight className="h-4 w-4" />
        </Link>
      </CardHeader>
    </Card>
  );
}
