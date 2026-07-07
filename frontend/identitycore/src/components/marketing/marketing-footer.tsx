import Link from "next/link";

const footerGroups = [
  {
    title: "Product",
    links: [
      ["Platform", "/platform"],
      ["How it works", "/how-it-works"],
      ["Templates", "/templates"],
      ["Solutions", "/solutions"],
    ],
  },
  {
    title: "Resources",
    links: [
      ["Security", "/security"],
      // ["Pricing", "/pricing"],
      ["Developers", "/developers"],
      ["Contact", "/contact"],
    ],
  },
  {
    title: "Company",
    links: [
      ["About", "/company"],
      ["Privacy", "/legal/privacy"],
      ["Terms", "/legal/terms"],
      ["Cookies", "/legal/cookies"],
    ],
  },
];

export function MarketingFooter() {
  return (
    <footer className="border-t bg-white py-12">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 sm:px-6 md:grid-cols-[1.2fr_2fr]">
        <div>
          <p className="text-sm font-semibold">IdentityCore</p>
          <p className="mt-3 max-w-sm text-sm leading-6 text-muted-foreground">
            Digital identity infrastructure for organizations that need control,
            privacy, provider flexibility, and trusted workflows.
          </p>
          <p className="mt-6 text-sm text-muted-foreground">
            © 2026 IdentityCore
          </p>
        </div>

        <div className="grid gap-8 sm:grid-cols-3">
          {footerGroups.map((group) => (
            <div key={group.title}>
              <p className="text-sm font-semibold">{group.title}</p>

              <div className="mt-4 grid gap-3">
                {group.links.map(([label, href]) => (
                  <Link
                    key={href}
                    href={href}
                    className="text-sm text-muted-foreground hover:text-foreground"
                  >
                    {label}
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </footer>
  );
}