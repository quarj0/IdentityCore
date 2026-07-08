"use client";

import { useState } from "react";
import { CodeBlock } from "@/components/docs/code-block";
import type { EndpointExample } from "@/data/endpoints";

interface LanguageExamplesProps {
  title: string;
  description?: string;
  examples: EndpointExample[];
}

export function LanguageExamples({
  title,
  description,
  examples,
}: LanguageExamplesProps) {
  const [activeExample, setActiveExample] = useState(examples[0]?.label);
  const selectedExample =
    examples.find((example) => example.label === activeExample) ?? examples[0];

  if (!selectedExample) {
    return null;
  }

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold">{title}</h2>
          {description ? (
            <p className="mt-2 max-w-2xl text-sm leading-7 text-slate-600">
              {description}
            </p>
          ) : null}
        </div>

        <div
          className="flex flex-wrap gap-2"
          role="tablist"
          aria-label={`${title} language examples`}
        >
          {examples.map((example) => {
            const isActive = example.label === selectedExample.label;

            return (
              <button
                key={example.label}
                type="button"
                role="tab"
                aria-selected={isActive}
                onClick={() => setActiveExample(example.label)}
                className={
                  isActive
                    ? "rounded-full bg-blue-600 px-3 py-1.5 text-sm font-medium text-white"
                    : "rounded-full border border-slate-200 px-3 py-1.5 text-sm text-slate-600 hover:border-slate-300 hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
                }
              >
                {example.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="mt-6">
        <CodeBlock
          title={selectedExample.label}
          language={selectedExample.language}
          code={selectedExample.code}
        />
      </div>
    </section>
  );
}
