"use client";

import { useEffect } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { AUTH_SESSION_EXPIRED_EVENT } from "@/lib/auth";

export function SessionExpiryBoundary() {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    const handleExpiry = () => {
      const query = searchParams.toString();
      const currentPath = `${pathname}${query ? `?${query}` : ""}`;
      const loginParams = new URLSearchParams({ reason: "session_expired" });
      if (pathname !== "/login") loginParams.set("returnTo", currentPath);
      window.location.assign(`/login?${loginParams.toString()}`);
    };

    window.addEventListener(AUTH_SESSION_EXPIRED_EVENT, handleExpiry);
    return () =>
      window.removeEventListener(AUTH_SESSION_EXPIRED_EVENT, handleExpiry);
  }, [pathname, searchParams]);

  return null;
}
