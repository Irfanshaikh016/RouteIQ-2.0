import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RouteIQ 2.0 — Cognitive Logistics Intelligence",
  description: "Cognitive, Graph-Aware, Self-Learning Route & Logistics Intelligence Platform for the North Eastern Region",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased bg-slate-950 text-slate-100 min-h-screen">
        {children}
      </body>
    </html>
  );
}
