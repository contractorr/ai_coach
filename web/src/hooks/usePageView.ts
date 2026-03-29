"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";
import { useToken } from "./useToken";

const TRACKED = new Set([
  "/",
  "/home",
  "/journal",
  "/learn",
  "/focus",
  "/goals",
  "/radar",
  "/research",
  "/intel",
  "/library",
  "/advisor",
  "/projects",
  "/settings",
]);

function shouldTrack(pathname: string) {
  return TRACKED.has(pathname) || pathname.startsWith("/learn/");
}

export function usePageView() {
  const pathname = usePathname();
  const token = useToken();
  const prev = useRef("");
  useEffect(() => {
    if (!token || !shouldTrack(pathname) || pathname === prev.current) return;
    prev.current = pathname;
    fetch(`${process.env.NEXT_PUBLIC_API_URL || ""}/api/v1/page-view`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ path: pathname }),
    }).catch(() => {});
  }, [pathname, token]);
}
