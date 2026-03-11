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
  const [guideOpen, setGuideOpen] = useState(false);
  const [bannerDismissed, setBannerDismissed] = useState(false);
  const [displayName, setDisplayName] = useState<string | null>(null);
  const skipGate = pathname === "/onboarding";
  const [gateChecked, setGateChecked] = useState(false);
  const showBanner = liteMode && !bannerDismissed && pathname !== "/onboarding";

  // Fetch display name from backend (prefers onboarding name over OAuth name)
  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    apiFetch<{ name: string | null }>("/api/user/me", {}, token).then((user) => {
      if (!cancelled && user.name) setDisplayName(user.name);
    }).catch(() => {});
    return () => { cancelled = true; };
  }, [token]);

  // Onboarding gate: redirect if no API key or no profile (e.g. after account deletion).
  useEffect(() => {
    if (!token || skipGate) return;
    let cancelled = false;
    apiFetch<{ llm_api_key_set: boolean; using_shared_key: boolean; has_profile: boolean }>("/api/settings", {}, token)
      .then((settings) => {
        if (cancelled) return;
        const hasAnyKey = settings.llm_api_key_set || settings.using_shared_key;
        if (!hasAnyKey || !settings.has_profile) {
          router.replace("/onboarding");
        } else {
          setGateChecked(true);
        }
      })
      .catch(() => {
        // Network error / 401 — don't redirect, let the page render.
        if (!cancelled) setGateChecked(true);
      });
    return () => { cancelled = true; };
  }, [token, skipGate, router]);

  return (
    <div className="h-screen">
      <AppHeader
        onOpenSettings={() => setSettingsOpen(true)}
        onToggleSidebar={() => setSidebarOpen((v) => !v)}
        onOpenGuide={() => setGuideOpen(true)}
      />
      <Sidebar open={sidebarOpen} onOpenChange={setSidebarOpen} displayName={displayName} disabled={skipGate} guideOpen={guideOpen} onGuideOpenChange={setGuideOpen} />
      {token && (
        <SettingsSheet
          open={settingsOpen}
          onOpenChange={setSettingsOpen}
          token={token}
        />
      )}
      {showBanner && (
        <div className="fixed top-12 left-0 right-0 z-30 border-b border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/80 px-4 py-1.5 lg:left-60">
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
      <main className={`h-full overflow-y-auto pt-12 lg:pl-60 ${showBanner ? "mt-8" : ""}`}>
        {(gateChecked || skipGate) ? children : null}
      </main>
    </div>
  );
}
