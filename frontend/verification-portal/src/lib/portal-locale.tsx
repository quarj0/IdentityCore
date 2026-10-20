"use client";

import {
  createContext,
  useContext,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import { resolveLocale, translate, type SupportedLocale } from "./i18n";

const InitialLocale = createContext<SupportedLocale>("en");

export function PortalLocaleProvider({
  locale,
  children,
}: {
  locale: SupportedLocale;
  children: ReactNode;
}) {
  return (
    <InitialLocale.Provider value={locale}>{children}</InitialLocale.Provider>
  );
}

function subscribe(onChange: () => void) {
  const observer = new MutationObserver(onChange);
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["lang"],
  });
  return () => observer.disconnect();
}

export function usePortalLocale() {
  const initial = useContext(InitialLocale);
  return useSyncExternalStore(
    subscribe,
    () => resolveLocale(document.documentElement.lang || initial),
    () => initial,
  );
}

export function PortalSkipLink() {
  const locale = usePortalLocale();
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-100 focus:rounded-xl focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-primary-foreground"
    >
      {translate(locale, "skip")}
    </a>
  );
}
