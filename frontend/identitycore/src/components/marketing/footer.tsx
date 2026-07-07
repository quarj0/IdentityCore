import Link from "next/link";

export function MarketingFooter() {
  return (
    <footer className="border-t py-8">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-6 sm:flex-row">
        <p className="text-sm text-muted-foreground">© 2026 IdentityCore</p>

        <div className="flex gap-6 text-sm text-muted-foreground">
          <Link href="/security" className="hover:text-foreground">
            Security
          </Link>
          <Link href="/company" className="hover:text-foreground">
            Company
          </Link>
          <Link href="/pricing" className="hover:text-foreground">
            Pricing
          </Link>
        </div>
      </div>
    </footer>
  );
}
