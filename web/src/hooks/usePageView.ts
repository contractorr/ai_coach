"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";
import { useToken } from "./useToken";

const TRACKED = new Set([
  "/",
  "/journal",
  "/focus",
  "/goals",
  "/radar",
  "/intel",
  "/library",
  "/settings",
]);

export function usePageView() {
  const pathname = usePathname();
  const token = useToken();
  const prev = useRef("");
  useEffect(() => {
    if (!token || !TRACKED.has(pathname) || pathname === prev.current) return;
    prev.current = pathname;
    fetch(`${process.env.NEXT_PUBLIC_API_URL || ""}/api/page-view`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ path: pathname }),
    }).catch(() => {});
  }, [pathname, token]);
}
