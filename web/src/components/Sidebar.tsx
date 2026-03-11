"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession } from "next-auth/react";
import {
  BookOpen,
  Brain,
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
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { guideCards, behindTheScenesCards } from "@/app/(dashboard)/onboarding/page";

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
  disabled,
}: {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  active: boolean;
  onClick: () => void;
  disabled?: boolean;
}) {
  if (disabled) {
    return (
      <span className="group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-sidebar-foreground/30 cursor-not-allowed">
        <Icon className="h-[18px] w-[18px] shrink-0 text-sidebar-foreground/20" />
        {label}
      </span>
    );
  }
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
  disabled,
  guideOpen,
  onGuideOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  displayName?: string | null;
  disabled?: boolean;
  guideOpen: boolean;
  onGuideOpenChange: (open: boolean) => void;
}) {
  const pathname = usePathname();
  const { data: session } = useSession();
  const user = session?.user;

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
        <div className="flex h-14 items-center justify-between px-4">
          <button
            onClick={() => !disabled && onGuideOpenChange(true)}
            disabled={disabled}
            className="flex items-center gap-2.5 rounded-lg transition-opacity hover:opacity-80 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sidebar-primary/10">
              <Brain className="h-[18px] w-[18px] text-sidebar-primary" />
            </div>
            <span className="text-[15px] font-semibold tracking-tight text-sidebar-foreground">StewardMe</span>
          </button>
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
                disabled={disabled}
              />
            ))}
          </div>
        </nav>

        {/* Footer */}
        <div className="shrink-0 border-t border-sidebar-border px-3 py-3 space-y-1">
          <NavItem
            href="/settings"
            label="Settings"
            icon={Settings}
            active={pathname === "/settings"}
            onClick={() => onOpenChange(false)}
            disabled={disabled}
          />

          {/* User + actions */}
          <div className="mt-1 flex items-center gap-2.5 rounded-lg px-3 py-2">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-sidebar-accent">
              <User className="h-3.5 w-3.5 text-sidebar-foreground/50" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="truncate text-[13px] font-medium text-sidebar-foreground">
                {displayName || user?.name || "User"}
              </p>
              {user?.email && (
                <p className="truncate text-[11px] text-sidebar-foreground/40">
                  {user.email}
                </p>
              )}
            </div>
            <div className="flex items-center gap-0.5 shrink-0">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => !disabled && onGuideOpenChange(true)}
                disabled={disabled}
                title="How this works"
                className="h-7 w-7 text-sidebar-foreground/30 hover:text-sidebar-foreground hover:bg-sidebar-accent"
              >
                <HelpCircle className="h-3.5 w-3.5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => signOut({ callbackUrl: "/login" })}
                title="Sign out"
                className="h-7 w-7 text-sidebar-foreground/30 hover:text-sidebar-foreground hover:bg-sidebar-accent"
              >
                <LogOut className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>

          <Dialog open={guideOpen} onOpenChange={onGuideOpenChange}>
            <DialogContent className="sm:max-w-2xl max-h-[85vh] overflow-y-auto gap-6">
              <div>
                <DialogTitle className="text-base">How this works</DialogTitle>
                <DialogDescription className="text-sm text-muted-foreground mt-1">
                  A quick overview of what StewardMe does and how to get the most out of it.
                </DialogDescription>
              </div>
              <div>
                <p className="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground/60">Getting started</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {guideCards.map(({ icon: Icon, title, description }) => (
                    <div key={title} className="flex gap-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                        <Icon className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">{title}</p>
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          {description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="border-t border-border" />
              <div>
                <p className="mb-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground/60">Working for you</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {behindTheScenesCards.map(({ icon: Icon, title, description }) => (
                    <div key={title} className="flex gap-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                        <Icon className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">{title}</p>
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          {description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-lg border bg-muted/50 p-3 text-xs text-muted-foreground leading-relaxed">
                <span className="font-medium text-foreground">Tip:</span>{" "}
                The more you journal and set goals, the sharper your brief gets.
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </aside>
    </>
  );
}
