import type { ReactNode } from "react";
import { DocsSidebar } from "./docs-sidebar";
import { MobileDocsNav } from "./mobile-docs-nav";
import { DocsSearch } from "./docs-search";
interface DocsLayoutProps {
  title: string;
  description: string;
  children: ReactNode;
}

export function DocsLayout({ title, description, children }: DocsLayoutProps) {
  return (
    <main id="main-content" className="mx-auto max-w-7xl px-4 py-12 sm:px-6">
      <div className="grid gap-10 lg:grid-cols-[260px_1fr]">
        <DocsSidebar />

        <div className="min-w-0">
          <MobileDocsNav />

          <div className="mt-10 lg:mt-0">
          
            <div className="mb-8">
              <DocsSearch />
            </div>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">
              {title}
            </h1>

            <p className="mt-5 max-w-3xl text-base leading-8 text-slate-600 sm:text-lg">
              {description}
            </p>

            <div className="mt-10 space-y-10">{children}</div>
          </div>
        </div>
      </div>
    </main>
  );
}
