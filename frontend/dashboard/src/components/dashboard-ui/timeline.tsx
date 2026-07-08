import { CheckCircle2 } from "lucide-react";

interface TimelineItem {
  title: string;
  description: string;
  time: string;
}

interface TimelineProps {
  items: TimelineItem[];
}

export function Timeline({ items }: TimelineProps) {
  return (
    <div className="space-y-4">
      {items.map((item) => (
        <div key={item.title} className="flex gap-3">
          <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
            <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
          </div>

          <div>
            <p className="text-sm font-medium">{item.title}</p>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              {item.description}
            </p>
            <p className="mt-1 text-xs text-slate-400">{item.time}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
