"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Beer, BarChart3, LayoutGrid, LogOut, Settings, History } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAuth } from "@/stores/auth";

const links = [
  { href: "/tables", label: "Mesas", icon: LayoutGrid },
  { href: "/orders", label: "Historial", icon: History },
  { href: "/report", label: "Corte", icon: BarChart3 },
  { href: "/admin", label: "Admin", adminOnly: true, icon: Settings },
];

function Avatar({ name }: { name?: string | null }) {
  const initials = (name ?? "P")
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
  return (
    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900/90 text-xs font-semibold text-white">
      {initials}
    </div>
  );
}

export function Nav() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/80 backdrop-blur-md shadow-sm shadow-slate-900/5">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-2.5">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-slate-900 text-white shadow-sm">
              <Beer className="h-4 w-4" />
            </div>
            <span className="text-sm font-semibold text-slate-700">POS Bar</span>
          </div>
          <nav className="flex items-center gap-1">
            {links
              .filter((l) => !l.adminOnly || user?.role === "admin")
              .map((l) => {
                const isActive = pathname.startsWith(l.href);
                const Icon = l.icon;
                return (
                  <Link
                    key={l.href}
                    href={l.href}
                    className={cn(
                      "group inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-300",
                      isActive
                        ? "bg-slate-900 text-white shadow-sm"
                        : "text-slate-600 hover:bg-slate-100",
                    )}
                  >
                    <Icon className={cn("h-4 w-4", isActive ? "text-white" : "text-slate-400 group-hover:text-slate-600")} />
                    {l.label}
                  </Link>
                );
              })}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Avatar name={user?.name} />
            <div className="hidden sm:flex flex-col leading-tight">
              <span className="text-xs font-medium text-slate-700">{user?.name ?? "Mesero"}</span>
              <span className="text-[10px] uppercase tracking-wide text-slate-400">{user?.role}</span>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="group"
            onClick={async () => {
              await logout();
              router.replace("/login");
            }}
          >
            <LogOut className="h-4 w-4 transition-transform group-hover:-translate-x-0.5" />
            <span className="hidden sm:inline">Salir</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
