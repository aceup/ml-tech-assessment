import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker
  output: 'standalone',

  // React strict mode
  reactStrictMode: true,
};

export default nextConfig;
