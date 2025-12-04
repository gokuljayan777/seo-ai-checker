import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,

  // Proxy /api/analyze -> http://localhost:8000/api/analyze/
  async rewrites() {
    return [
      {
        source: "/api/analyze",            // request path in Next app
        destination: "http://localhost:8000/api/analyze/", // target backend
      },
      // optional: proxy any other backend API paths
      // {
      //   source: "/api/:path*",
      //   destination: "http://localhost:8000/api/:path*",
      // },
    ];
  },
};

export default nextConfig;
