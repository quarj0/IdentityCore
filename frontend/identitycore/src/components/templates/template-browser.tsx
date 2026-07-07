"use client";

import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { Input } from "@identitycore/ui";
import { TemplateCard } from "@/components/marketing/template-card";
import { workflowTemplates } from "@/data/templates";

const categories = [
  "All",
  "Financial services",
  "Education",
  "HR",
  "Healthcare",
  "Government",
  "General",
];

export function TemplateBrowser() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All");

  const filteredTemplates = useMemo(() => {
    return workflowTemplates.filter((template) => {
      const matchesCategory =
        category === "All" || template.category === category;

      const searchText = [
        template.title,
        template.category,
        template.description,
        ...template.tags,
        ...template.required,
        ...template.providers,
      ]
        .join(" ")
        .toLowerCase();

      const matchesSearch = searchText.includes(query.toLowerCase());

      return matchesCategory && matchesSearch;
    });
  }, [query, category]);

  return (
    <div>
      <div className="rounded-[2rem] border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="relative lg:w-96">
            <Search
              className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden="true"
            />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search templates, providers, or use cases..."
              className="h-11 rounded-2xl pl-10"
              aria-label="Search workflow templates"
            />
          </div>

          <div
            className="flex gap-2 overflow-x-auto pb-1"
            aria-label="Template categories"
          >
            {categories.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => setCategory(item)}
                className={
                  item === category
                    ? "shrink-0 rounded-full bg-blue-600 px-4 py-2 text-sm font-medium text-white"
                    : "shrink-0 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground"
                }
              >
                {item}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-8 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredTemplates.map((template) => (
          <TemplateCard key={template.slug} {...template} />
        ))}
      </div>

      {filteredTemplates.length === 0 ? (
        <div className="mt-12 rounded-3xl border border-slate-200 bg-slate-50 p-8 text-center">
          <p className="font-medium">No templates found</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Try a different search term or category.
          </p>
        </div>
      ) : null}
    </div>
  );
}