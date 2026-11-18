import { describe, expect, it } from "vitest";

import { formatCOP, todayBogota } from "@/lib/utils";

describe("formatCOP", () => {
  it("formatea pesos enteros sin decimales", () => {
    const out = formatCOP(15000);
    expect(out).toContain("15");
    expect(out).not.toContain(",00");
  });

  it("todayBogota retorna yyyy-mm-dd", () => {
    expect(todayBogota()).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});
