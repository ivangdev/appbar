import type { NextConfig } from "next";

// URL interna (server-side) a la que Next reenvia /api/* -> backend.
// En dev local apunta al backend en localhost; en docker-compose a http://backend:8000.
const API_INTERNAL_URL =
  process.env.API_INTERNAL_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    // Proxy /api/* -> backend, para que la cookie HttpOnly viaje en el mismo origen.
    return [
      { source: "/api/:path*", destination: `${API_INTERNAL_URL}/:path*` },
    ];
  },
};

export default nextConfig;
