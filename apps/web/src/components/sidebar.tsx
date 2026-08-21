"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { NAV_ITEMS } from "@/components/nav-config";
import { useLogout } from "@/lib/auth";
import type { User } from "@/lib/types";
import { cn } from "@/lib/utils";

export function Sidebar({ user }: { user: User }) {
  const pathname = usePathname();
  const router = useRouter();
  const logout = useLogout();

  async function onLogout() {
    await logout.mutateAsync();
    router.push("/login");
  }

  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar">
      <div className="px-4 py-5">
        <p className="text-sm font-semibold tracking-tight text-sidebar-foreground">The21Secrets</p>
        <p className="text-xs text-muted-foreground">AI Ads OS</p>
      </div>
      <nav className="flex-1 space-y-0.5 px-2">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center justify-between rounded-md px-2.5 py-1.5 text-sm transition-colors",
                active
                  ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
              )}
            >
              <span>{item.label}</span>
              {item.comingInPhase !== null && (
                <span className="text-[10px] text-muted-foreground">P{item.comingInPhase}</span>
              )}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-sidebar-border px-4 py-3">
        <p className="truncate text-xs text-muted-foreground">{user.email}</p>
        <Button
          variant="ghost"
          size="sm"
          className="mt-1 h-7 w-full justify-start px-0 text-xs text-muted-foreground hover:text-foreground"
          onClick={onLogout}
        >
          Sign out
        </Button>
      </div>
    </aside>
  );
}
