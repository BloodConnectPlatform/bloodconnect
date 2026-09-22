import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  env: {
    WHATSAPP_NUMBER: process.env.WHATSAPP_NUMBER || process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || "919843883304",
    NEXT_PUBLIC_WHATSAPP_NUMBER: process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || process.env.WHATSAPP_NUMBER || "919843883304",
  },
  allowedDevOrigins: [
    "*.trycloudflare.com",
    "trycloudflare.com",
    "*.loca.lt",
    "*.ngrok-free.app",
    "*.ngrok.io",
    "*.ngrok.app",
    "localhost",
    "127.0.0.1",
    "localhost:3000",
    "127.0.0.1:3000",
  ],
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${process.env.INTERNAL_API_URL || "http://127.0.0.1:8000"}/api/v1/:path*`,
      },
      {
        source: "/webhooks/:path*",
        destination: `${process.env.INTERNAL_API_URL || "http://127.0.0.1:8000"}/webhooks/:path*`,
      },
    ];
  },
};

export default nextConfig;
