import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { BadgeCheck } from "lucide-react";
import {
  Badge,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";

interface TemplateCardProps {
  slug: string;
  title: string;
  category: string;
  description: string;
  icon: LucideIcon;
  tags: string[];
  href?: string;
}

export function TemplateCard({
  slug,
  title,
  category,
  description,
  icon: Icon,
  tags,
  href,
}: TemplateCardProps) {
  return (
    <Card className="group rounded-3xl border-slate-200 bg-white p-2 shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl">
      <CardHeader className="p-6">
        <div className="mb-6 flex items-center justify-between">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
            <Icon className="h-5 w-5" />
          </div>

          <Badge variant="secondary" className="rounded-full">
            Official
          </Badge>
        </div>

        <p className="text-sm font-medium text-blue-600">{category}</p>
        <CardTitle className="mt-2">{title}</CardTitle>
        <CardDescription className="pt-2 leading-7">
          {description}
        </CardDescription>
      </CardHeader>

      <CardContent className="px-6 pb-6">
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <span
              key={tag}
              className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700"
            >
              {tag}
            </span>
          ))}
        </div>

        <div className="mt-6 flex items-center justify-between border-t pt-5">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <BadgeCheck className="h-4 w-4 text-blue-600" />
            Ready to clone
          </div>

          <Link
            href={href ?? `/templates/${slug}`}
            className="text-sm font-medium text-blue-600 hover:text-blue-700"
          >
            Preview →
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
