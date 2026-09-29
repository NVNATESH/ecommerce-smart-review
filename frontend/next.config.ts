import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Three.js + Recharts are client-only; keep them out of the server bundle.
  transpilePackages: ["three"],
};

export default nextConfig;
