"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/stores/auth";

export default function HomePage() {
  const router = useRouter();
  const { user, loading, load } = useAuth();

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!loading) router.replace(user ? "/tables" : "/login");
  }, [loading, user, router]);

  return <div className="p-8 text-sm text-slate-500">Cargando...</div>;
}
