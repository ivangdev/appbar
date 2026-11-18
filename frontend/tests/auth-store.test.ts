import { beforeEach, describe, expect, it, vi } from "vitest";

const api = {
  login: vi.fn(),
  me: vi.fn(),
  logout: vi.fn(),
};

vi.mock("@/lib/api", () => ({
  authApi: {
    login: (...args: unknown[]) => api.login(...args),
    me: (...args: unknown[]) => api.me(...args),
    logout: (...args: unknown[]) => api.logout(...args),
  },
  apiError: (error: unknown) =>
    error instanceof Error ? error.message : "error",
}));

const adminUser = {
  id: "u1",
  name: "Admin",
  email: "admin@posbar.com",
  role: "admin" as const,
  is_active: true,
};

describe("useAuth store", () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    const { useAuth } = await import("@/stores/auth");
    useAuth.setState({ user: null, loading: true, error: null });
  });

  it("login exitoso guarda el usuario y retorna true", async () => {
    const { useAuth } = await import("@/stores/auth");
    api.login.mockResolvedValue({ access_token: "t", token_type: "bearer" });
    api.me.mockResolvedValue(adminUser);

    const ok = await useAuth.getState().login("admin@posbar.com", "x");

    expect(ok).toBe(true);
    expect(useAuth.getState().user?.email).toBe("admin@posbar.com");
    expect(useAuth.getState().error).toBeNull();
  });

  it("login fallido guarda el error y retorna false", async () => {
    const { useAuth } = await import("@/stores/auth");
    api.login.mockRejectedValue(new Error("Credenciales invalidas"));

    const ok = await useAuth.getState().login("admin@posbar.com", "mala");

    expect(ok).toBe(false);
    expect(useAuth.getState().user).toBeNull();
    expect(useAuth.getState().error).toBe("Credenciales invalidas");
  });

  it("logout limpia el usuario aun si la API falla", async () => {
    const { useAuth } = await import("@/stores/auth");
    useAuth.setState({ user: adminUser });
    api.logout.mockRejectedValue(new Error("boom"));

    await useAuth.getState().logout();

    expect(useAuth.getState().user).toBeNull();
  });
});
