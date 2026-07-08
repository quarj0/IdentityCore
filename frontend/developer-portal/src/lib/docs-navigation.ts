import { docsNav, type DocsNavItem } from "@/data/docs-nav";

export function isDocsPathActive(pathname: string, href: string) {
  if (href === "/") {
    return pathname === href;
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

export function getDocsNavItems() {
  return docsNav.flatMap((group) => group.items);
}

export function getPrimaryDocsItem(pathname: string): DocsNavItem | undefined {
  return getDocsNavItems().find((item) => isDocsPathActive(pathname, item.href));
}
