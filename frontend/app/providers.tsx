"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { useAuth } from "@/stores/auth";

/** Cierra la sesion local y vuelve al login cuando la API responde 401. */
function SessionWatcher() {
  const router = useRouter();

  useEffect(() => {
    const onUnauthorized = () => {
      useAuth.setState({ user: null, loading: false });
      router.replace("/login");
    };
    window.addEventListener("posbar:unauthorized", onUnauthorized);
    return () => window.removeEventListener("posbar:unauthorized", onUnauthorized);
  }, [router]);

  return null;
}

export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(() => new QueryClient());
  return (
    <QueryClientProvider client={client}>
      <SessionWatcher />
      {children}
    </QueryClientProvider>
  );
}
