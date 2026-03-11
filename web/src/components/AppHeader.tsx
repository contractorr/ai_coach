"use client";

import { Brain, Menu, Settings, LogOut } from "lucide-react";
import { signOut } from "next-auth/react";
import { Button } from "@/components/ui/button";

export function AppHeader({
  onOpenSettings,
  onToggleSidebar,
  onOpenGuide,
}: {
  onOpenSettings: () => void;
  onToggleSidebar: () => void;
  onOpenGuide?: () => void;
}) {
  return (
    <header className="fixed inset-x-0 top-0 z-40 flex h-12 items-center justify-between border-b bg-background px-4 lg:left-60">
      <div className="flex items-center gap-1.5">
        <Button variant="ghost" size="icon" onClick={onToggleSidebar} className="-ml-2 lg:hidden">
          <Menu className="h-4 w-4" />
        </Button>
        <button
          onClick={onOpenGuide}
          className="flex items-center gap-2 transition-opacity hover:opacity-80 lg:hidden"
        >
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary/10">
            <Brain className="h-3.5 w-3.5 text-primary" />
          </div>
          <span className="text-sm font-semibold text-foreground">StewardMe</span>
        </button>
      </div>
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="icon" onClick={onOpenSettings} title="Settings">
          <Settings className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => signOut({ callbackUrl: "/login" })}
          title="Sign out"
        >
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}
