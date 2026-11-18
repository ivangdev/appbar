import { afterEach, describe, expect, it, vi } from "vitest";

import { tablesSocketUrl } from "@/hooks/use-tables-socket";

describe("tablesSocketUrl", () => {
  const original = process.env.NEXT_PUBLIC_API_URL;

  afterEach(() => {
    if (original === undefined) delete process.env.NEXT_PUBLIC_API_URL;
    else process.env.NEXT_PUBLIC_API_URL = original;
    vi.unstubAllGlobals();
  });

  it("convierte http(s) -> ws(s) y apunta a /ws/tables", () => {
    process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000";
    expect(tablesSocketUrl()).toBe("ws://localhost:8000/ws/tables");
  });

  it("soporta https -> wss", () => {
    process.env.NEXT_PUBLIC_API_URL = "https://bar.local";
    expect(tablesSocketUrl()).toBe("wss://bar.local/ws/tables");
  });

  it("sin env ni window cae a ruta relativa", () => {
    delete process.env.NEXT_PUBLIC_API_URL;
    expect(tablesSocketUrl()).toBe("/ws/tables");
  });

  it("con NEXT_PUBLIC_API_URL vacio usa el origin actual (regresion)", () => {
    // En prod el backend se sirve tras el mismo origen: la cadena vacia debe
    // caer al origin del navegador y no generar una URL relativa invalida.
    process.env.NEXT_PUBLIC_API_URL = "";
    vi.stubGlobal("window", { location: { origin: "https://bar.local" } });
    expect(tablesSocketUrl()).toBe("wss://bar.local/ws/tables");
  });
});
