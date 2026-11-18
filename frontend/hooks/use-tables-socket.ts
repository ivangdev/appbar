"use client";

// Hook WebSocket al tablero de mesas. La autenticacion viaja en la cookie
// HttpOnly del handshake (el navegador la adjunta automaticamente); NUNCA se
// pasa el token por la URL.
import { useEffect, useRef } from "react";

import type { TableEvent } from "@/lib/types";

/** URL del canal WS. En prod (mismo origen tras Caddy) usa el origin actual. */
export function tablesSocketUrl(): string {
  const base =
    process.env.NEXT_PUBLIC_API_URL ||
    (typeof window !== "undefined" ? window.location.origin : "");
  return base.replace(/^http/, "ws") + "/ws/tables";
}

export function useTablesSocket(onEvent: (event: TableEvent) => void): void {
  const handler = useRef(onEvent);

  useEffect(() => {
    handler.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    let socket: WebSocket | null = null;
    let closed = false;
    let retry: ReturnType<typeof setTimeout>;
    let attempt = 0;

    const connect = () => {
      socket = new WebSocket(tablesSocketUrl());
      socket.onopen = () => {
        attempt = 0;
      };
      socket.onmessage = (msg) => {
        try {
          handler.current(JSON.parse(msg.data as string) as TableEvent);
        } catch {
          // ignora mensajes no-JSON
        }
      };
      socket.onclose = (event) => {
        if (closed) return;
        // 1008 = politica de la app: token ausente/expirado o usuario inactivo.
        if (event.code === 1008) {
          closed = true;
          window.dispatchEvent(new Event("posbar:unauthorized"));
          return;
        }
        // Reconexion con backoff progresivo (2s, 4s, 8s, max 10s).
        attempt += 1;
        retry = setTimeout(connect, Math.min(10_000, 2_000 * 2 ** (attempt - 1)));
      };
    };

    connect();
    return () => {
      closed = true;
      clearTimeout(retry);
      socket?.close();
    };
  }, []);
}
