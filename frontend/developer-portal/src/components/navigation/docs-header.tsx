import Link from "next/link";
import { BookOpen } from "lucide-react";
import { siteConfig } from "@/lib/site-config";

export function DocsHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center px-4 sm:px-6">
        <Link
          href="/"
          className="flex items-center gap-3 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
          aria-label="IdentityCore developer portal home"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-white">
            <BookOpen className="h-5 w-5" />
          </div>

          <div>
            <p className="text-sm font-semibold">IdentityCore</p>
            <p className="text-xs text-slate-500">Developer Portal</p>
          </div>
        </Link>

        <nav className="ml-auto hidden items-center gap-6 text-sm text-slate-600 sm:flex">
          <Link href="/quickstart" className="hover:text-slate-950">
            Getting started
          </Link>
          <Link href="/api-reference" className="hover:text-slate-950">
            API
          </Link>
          <Link href="/webhooks" className="hover:text-slate-950">
            Webhooks
          </Link>
          <a href={siteConfig.marketingSiteUrl} className="hover:text-slate-950">
            Main site
          </a>
        </nav>
      </div>
    </header>
  );
}
