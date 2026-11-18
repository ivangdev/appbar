import { afterEach, describe, expect, it } from "vitest";

import { tablesSocketUrl } from "@/hooks/use-tables-socket";

describe("tablesSocketUrl", () => {
  const original = process.env.NEXT_PUBLIC_API_URL;

  afterEach(() => {
    if (original === undefined) delete process.env.NEXT_PUBLIC_API_URL;
    else process.env.NEXT_PUBLIC_API_URL = original;
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
});
