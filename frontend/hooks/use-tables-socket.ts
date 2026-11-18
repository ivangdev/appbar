"use client";

// Hook WebSocket al tablero de mesas. La autenticacion viaja en la cookie
// HttpOnly del handshake (el navegador la adjunta automaticamente); NUNCA se
// pasa el token por la URL.
import { useEffect, useRef } from "react";

import type { TableEvent } from "@/lib/types";

/** URL del canal WS. En prod (mismo origen tras Caddy) usa el origin actual. */
export function tablesSocketUrl(): string {
  const base =
    process.env.NEXT_PUBLIC_API_URL ??
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

    const connect = () => {
      socket = new WebSocket(tablesSocketUrl());
      socket.onmessage = (msg) => {
        try {
          handler.current(JSON.parse(msg.data as string) as TableEvent);
        } catch {
          // ignora mensajes no-JSON
        }
      };
      socket.onclose = () => {
        if (!closed) retry = setTimeout(connect, 2000);
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
