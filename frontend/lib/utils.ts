export { cn } from "cn"

export function formatCOP(value: number): string {
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP" }).format(value)
}

const BOGOTA_TZ = "America/Bogota"

/** Fecha (YYYY-MM-DD) del dia en curso en America/Bogota, no en la TZ del equipo. */
export function todayBogota(now: Date = new Date()): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: BOGOTA_TZ,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(now)
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? ""
  return `${get("year")}-${get("month")}-${get("day")}`
}
