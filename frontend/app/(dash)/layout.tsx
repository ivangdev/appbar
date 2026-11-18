"use client";

import { Nav } from "@/components/nav";
import { RequireAuth } from "@/components/require-auth";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RequireAuth>
      <Nav />
      <main className="mx-auto max-w-6xl p-4">{children}</main>
    </RequireAuth>
  );
}
