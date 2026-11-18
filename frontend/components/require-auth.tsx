"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/stores/auth";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, loading, load } = useAuth();

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading || !user) {
    return <div className="p-8 text-sm text-slate-500">Cargando...</div>;
  }
  return <>{children}</>;
}
