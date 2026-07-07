import Link from "next/link";
import { ArrowLeft, SearchX } from "lucide-react";
import { Button, Card, CardContent } from "@identitycore/ui";
import { MarketingFooter } from "@/components/marketing/marketing-footer";
import { MarketingHeader } from "@/components/marketing/marketing-header";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader />

      <main id="main-content" className="relative overflow-hidden">
        <div className="absolute inset-x-0 top-0 -z-10 h-[520px] bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.14),transparent_34%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]" />

        <section className="mx-auto flex min-h-[70vh] max-w-4xl items-center px-4 py-20 sm:px-6">
          <Card className="w-full rounded-[2rem] border-slate-200 bg-white shadow-[0_24px_80px_rgba(15,23,42,0.10)]">
            <CardContent className="p-8 text-center sm:p-12">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
                <SearchX className="h-6 w-6" />
              </div>

              <h1 className="mt-6 text-4xl font-semibold tracking-tight sm:text-5xl">
                Page not found.
              </h1>

              <p className="mx-auto mt-4 max-w-xl text-base leading-7 text-muted-foreground">
                The page you are looking for does not exist or may have moved.
                Return to the homepage or explore the IdentityCore platform.
              </p>

              <div className="mt-8 flex flex-wrap justify-center gap-3">
                <Button asChild size="lg" className="rounded-xl">
                  <Link href="/">
                    <ArrowLeft className="h-4 w-4" />
                    Back home
                  </Link>
                </Button>

                <Button
                  asChild
                  variant="outline"
                  size="lg"
                  className="rounded-xl"
                >
                  <Link href="/platform">Explore platform</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </section>
      </main>

      <MarketingFooter />
    </div>
  );
}
