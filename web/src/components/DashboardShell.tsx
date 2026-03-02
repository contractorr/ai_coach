"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { X } from "lucide-react";
import { useToken } from "@/hooks/useToken";
import { usePageView } from "@/hooks/usePageView";
import { useLiteMode } from "@/hooks/useLiteMode";
import { AppHeader } from "@/components/AppHeader";
import { Sidebar } from "@/components/Sidebar";
import { SettingsSheet } from "@/components/SettingsSheet";
import { apiFetch } from "@/lib/api";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const token = useToken();
  usePageView();
  const pathname = usePathname();
  const router = useRouter();
  const liteMode = useLiteMode();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [bannerDismissed, setBannerDismissed] = useState(false);
  const skipGate = pathname === "/onboarding" || pathname === "/settings";
  const [gateChecked, setGateChecked] = useState(skipGate);
  const showBanner = liteMode && !bannerDismissed && pathname !== "/onboarding";

  // Onboarding gate: redirect to /onboarding if user lacks API key or profile.
  // Runs once on mount for all dashboard pages (not just /).
  useEffect(() => {
    if (!token || skipGate) return;
    let cancelled = false;
    Promise.allSettled([
      apiFetch<{ llm_api_key_set: boolean; using_shared_key: boolean }>("/api/settings", {}, token),
      apiFetch<{ has_profile: boolean }>("/api/onboarding/profile-status", {}, token),
    ]).then(([settingsRes, profileRes]) => {
      if (cancelled) return;
      const hasAnyKey =
        settingsRes.status === "fulfilled" &&
        (settingsRes.value.llm_api_key_set || settingsRes.value.using_shared_key);
      const noProfile =
        profileRes.status === "fulfilled" && !profileRes.value.has_profile;
      if (!hasAnyKey || noProfile) {
        router.replace("/onboarding");
      } else {
        setGateChecked(true);
      }
    });
    return () => { cancelled = true; };
  }, [token, skipGate, router]);

  return (
    <div className="h-screen">
      <AppHeader
        onOpenSettings={() => setSettingsOpen(true)}
        onToggleSidebar={() => setSidebarOpen((v) => !v)}
      />
      <Sidebar open={sidebarOpen} onOpenChange={setSidebarOpen} />
      {token && (
        <SettingsSheet
          open={settingsOpen}
          onOpenChange={setSettingsOpen}
          token={token}
        />
      )}
      {showBanner && (
        <div className="fixed top-12 left-0 right-0 z-30 border-b border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/80 px-4 py-1.5">
          <div className="relative flex items-center justify-center text-xs text-amber-800 dark:text-amber-200">
            <span className="text-center">
              Using lite mode (Haiku) &mdash; responses may be less detailed.{" "}
              <Link href="/settings" className="underline hover:text-amber-900 dark:hover:text-amber-100">
                Add your API key
              </Link>{" "}
              for the full experience.
            </span>
            <button onClick={() => setBannerDismissed(true)} className="absolute right-0 shrink-0 hover:text-amber-900 dark:hover:text-amber-100">
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}
      <main className={`h-full overflow-y-auto pt-12 ${showBanner ? "mt-8" : ""}`}>
        {gateChecked ? children : null}
      </main>
    </div>
  );
}
