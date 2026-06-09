import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Proxy /_/backend to localhost only during local development.
  // In production, NEXT_PUBLIC_API_URL is used directly.
  ...(process.env.NODE_ENV === "development" && {
    async rewrites() {
      return [
        {
          source: "/_/backend/:path*",
          destination: "http://127.0.0.1:8000/:path*",
        },
      ];
    },
  }),
};

export default nextConfig;
