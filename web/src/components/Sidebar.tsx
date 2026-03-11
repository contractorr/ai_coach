"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession } from "next-auth/react";
import {
  BookOpen,
  FileText,
  HelpCircle,
  Home,
  Newspaper,
  Settings,
  Target,
  X,
  LogOut,
  User,
} from "lucide-react";
import { signOut } from "next-auth/react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTitle,
} from "@/components/ui/sheet";
import { guideCards } from "@/app/(dashboard)/onboarding/page";

const primaryNav = [
  { href: "/home", label: "Home", icon: Home },
  { href: "/focus", label: "Focus", icon: Target },
  { href: "/radar", label: "Radar", icon: Newspaper },
  { href: "/library", label: "Library", icon: FileText },
  { href: "/journal", label: "Journal", icon: BookOpen },
];

function NavItem({
  href,
  label,
  icon: Icon,
  active,
  onClick,
}: {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <Link
      href={href}
      onClick={onClick}
      className={cn(
        "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all",
        active
          ? "bg-sidebar-accent text-sidebar-accent-foreground"
          : "text-sidebar-foreground/60 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
      )}
    >
      {active && (
        <span className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-sidebar-primary" />
      )}
      <Icon className={cn("h-[18px] w-[18px] shrink-0", active ? "text-sidebar-primary" : "text-sidebar-foreground/40 group-hover:text-sidebar-foreground/60")} />
      {label}
    </Link>
  );
}

export function Sidebar({
  open,
  onOpenChange,
  displayName,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  displayName?: string | null;
}) {
  const pathname = usePathname();
  const { data: session } = useSession();
  const user = session?.user;
  const [guideOpen, setGuideOpen] = useState(false);

  return (
    <>
      {/* Overlay backdrop (mobile only — sidebar is pinned on lg+) */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-[2px] lg:hidden"
          onClick={() => onOpenChange(false)}
        />
      )}

      {/* Slide-out sidebar — pinned open on lg+ */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-60 flex-col border-r border-sidebar-border bg-sidebar transition-transform duration-200 ease-out lg:translate-x-0 lg:z-30",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Header */}
        <div className="flex h-12 items-center justify-between border-b border-sidebar-border px-4">
          <span className="text-sm font-bold tracking-tight text-sidebar-primary">StewardMe</span>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onOpenChange(false)}
            className="h-7 w-7 text-sidebar-foreground/40 hover:text-sidebar-foreground hover:bg-sidebar-accent lg:hidden"
          >
            <X className="h-3.5 w-3.5" />
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex flex-1 flex-col gap-6 overflow-y-auto px-3 py-4">
          <div className="flex flex-col gap-0.5">
            {primaryNav.map((item) => (
              <NavItem
                key={item.href}
                {...item}
                active={pathname === item.href}
                onClick={() => onOpenChange(false)}
              />
            ))}
          </div>
        </nav>

        {/* Footer */}
        <div className="shrink-0 border-t border-sidebar-border p-3 space-y-1">
          <NavItem
            href="/settings"
            label="Settings"
            icon={Settings}
            active={pathname === "/settings"}
            onClick={() => onOpenChange(false)}
          />
          <button
            onClick={() => setGuideOpen(true)}
            className="group relative flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-sidebar-foreground/60 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground transition-all"
          >
            <HelpCircle className="h-[18px] w-[18px] shrink-0 text-sidebar-foreground/40 group-hover:text-sidebar-foreground/60" />
            How this works
          </button>

          <Sheet open={guideOpen} onOpenChange={setGuideOpen}>
            <SheetContent side="left" showCloseButton={false} className="w-60 p-0 gap-0">
              <div className="flex items-center justify-between border-b px-4 py-3">
                <SheetTitle className="text-sm font-semibold">How this works</SheetTitle>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => setGuideOpen(false)}
                >
                  <X className="h-3.5 w-3.5" />
                </Button>
              </div>
              <div className="space-y-4 overflow-y-auto px-4 py-4">
                {guideCards.map(({ icon: Icon, title, description }) => (
                  <div key={title} className="flex gap-3">
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-muted">
                      <Icon className="h-3.5 w-3.5 text-muted-foreground" />
                    </div>
                    <div>
                      <p className="text-xs font-medium">{title}</p>
                      <p className="text-[11px] text-muted-foreground leading-relaxed">
                        {description}
                      </p>
                    </div>
                  </div>
                ))}
                <div className="rounded-lg border bg-muted/50 p-2.5 text-[11px] text-muted-foreground leading-relaxed">
                  <span className="font-medium text-foreground">Tip:</span>{" "}
                  The more you journal and set goals, the sharper your brief gets.
                </div>
              </div>
            </SheetContent>
          </Sheet>

          {/* User + sign out */}
          <div className="mt-2 flex items-center gap-2.5 rounded-lg px-3 py-2">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-sidebar-accent">
              <User className="h-3.5 w-3.5 text-sidebar-foreground/50" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="truncate text-sm font-medium text-sidebar-foreground">
                {displayName || user?.name || "User"}
              </p>
              {user?.email && (
                <p className="truncate text-[11px] text-sidebar-foreground/40">
                  {user.email}
                </p>
              )}
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => signOut({ callbackUrl: "/login" })}
              title="Sign out"
              className="h-7 w-7 shrink-0 text-sidebar-foreground/30 hover:text-sidebar-foreground hover:bg-sidebar-accent"
            >
              <LogOut className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </aside>
    </>
  );
}
