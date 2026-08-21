"use client";

import { ChevronsLeft, ChevronsRight, LogOut } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { NAV_ITEMS } from "@/components/nav-config";
import { useLogout } from "@/lib/auth";
import type { User } from "@/lib/types";
import { cn } from "@/lib/utils";

const COLLAPSE_KEY = "the21os:sidebar-collapsed";

export function Sidebar({ user }: { user: User }) {
  const pathname = usePathname();
  const router = useRouter();
  const logout = useLogout();
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    // Reading localStorage can't happen during the initial render (SSR has
    // no localStorage, and reading it synchronously on the client would
    // mismatch the server-rendered "expanded" HTML) — this post-mount
    // update is the correct pattern here, not the effect this lint rule
    // usually warns about.
    try {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setCollapsed(localStorage.getItem(COLLAPSE_KEY) === "1");
    } catch {
      // localStorage unavailable — stay expanded
    }
  }, []);

  function toggleCollapsed() {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(COLLAPSE_KEY, next ? "1" : "0");
      } catch {
        // ignore — per-viewer convenience only
      }
      return next;
    });
  }

  async function onLogout() {
    await logout.mutateAsync();
    router.push("/login");
  }

  const initial = user.email.charAt(0).toUpperCase();

  return (
    <aside
      className={cn(
        "flex h-screen shrink-0 flex-col border-r border-sidebar-border bg-sidebar transition-[width] duration-200",
        collapsed ? "w-16" : "w-64",
      )}
    >
      <div className="flex items-center gap-2.5 px-4 py-5">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-sidebar-primary to-[oklch(0.6_0.18_300)] text-xs font-heading font-bold text-primary-foreground shadow-[0_0_16px_-2px_oklch(0.68_0.18_258_/_60%)]">
          21
        </span>
        {!collapsed && (
          <div className="min-w-0">
            <p className="font-heading text-sm font-semibold leading-tight tracking-tight text-sidebar-foreground">
              The21OS
            </p>
            <p className="text-[11px] leading-tight text-muted-foreground">AI Ads</p>
          </div>
        )}
      </div>

      <nav className="flex-1 space-y-0.5 px-2">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? item.label : undefined}
              className={cn(
                "flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-sm transition-colors",
                collapsed && "justify-center",
                active
                  ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
              )}
            >
              <Icon className={cn("size-4 shrink-0", active && "text-sidebar-primary")} />
              {!collapsed && (
                <>
                  <span className="min-w-0 flex-1 truncate">{item.label}</span>
                  {item.comingInPhase !== null && (
                    <Badge
                      variant="secondary"
                      className="h-4 shrink-0 rounded-full px-1.5 text-[10px] text-muted-foreground"
                    >
                      P{item.comingInPhase}
                    </Badge>
                  )}
                </>
              )}
            </Link>
          );
        })}
      </nav>

      <button
        type="button"
        onClick={toggleCollapsed}
        className="mx-2 mb-1 flex items-center justify-center rounded-lg py-1.5 text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
      >
        {collapsed ? <ChevronsRight className="size-4" /> : <ChevronsLeft className="size-4" />}
      </button>

      <div className="border-t border-sidebar-border p-3">
        <div className={cn("flex items-center gap-2", collapsed && "justify-center")}>
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-sidebar-accent text-xs font-medium text-sidebar-accent-foreground">
            {initial}
          </span>
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-medium text-sidebar-foreground">{user.email}</p>
              <p className="text-[11px] text-muted-foreground">Administrator</p>
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={onLogout}
          title={collapsed ? "Sign out" : undefined}
          className={cn(
            "mt-2 flex items-center gap-1.5 rounded-md text-xs text-destructive/80 transition-colors hover:text-destructive",
            collapsed ? "w-full justify-center py-1" : "px-0",
          )}
        >
          <LogOut className="size-3.5" />
          {!collapsed && "Sign out"}
        </button>
      </div>
    </aside>
  );
}
