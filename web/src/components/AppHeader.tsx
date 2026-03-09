"use client";

import { Menu, Settings, LogOut } from "lucide-react";
import { signOut } from "next-auth/react";
import { Button } from "@/components/ui/button";

export function AppHeader({
  onOpenSettings,
  onToggleSidebar,
}: {
  onOpenSettings: () => void;
  onToggleSidebar: () => void;
}) {
  return (
    <header className="fixed inset-x-0 top-0 z-40 flex h-12 items-center justify-between border-b bg-background px-4 lg:left-60">
      <div className="flex items-center gap-1.5">
        <Button variant="ghost" size="icon" onClick={onToggleSidebar} className="-ml-2 lg:hidden">
          <Menu className="h-4 w-4" />
        </Button>
        <span className="text-sm font-semibold text-primary lg:hidden">StewardMe</span>
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
