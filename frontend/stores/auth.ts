"use client";

import { create } from "zustand";

import { authApi, apiError } from "@/lib/api";
import type { User } from "@/lib/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
  load: () => Promise<void>;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  loading: true,
  error: null,
  load: async () => {
    try {
      const user = await authApi.me();
      set({ user, loading: false, error: null });
    } catch {
      set({ user: null, loading: false });
    }
  },
  login: async (email, password) => {
    try {
      await authApi.login(email, password);
      const user = await authApi.me();
      set({ user, error: null });
      return true;
    } catch (error) {
      set({ error: apiError(error) });
      return false;
    }
  },
  logout: async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignoramos fallos de red: la sesion local se limpia igual.
    } finally {
      set({ user: null });
    }
  },
}));
