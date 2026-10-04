import type { Metadata } from "next";
import { AuthProvider } from "@/lib/auth";
import "./globals.css";

export const metadata: Metadata = {
  title: "43v3rB3tz — Soccer predictions & analysis",
  description:
    "Match predictions across 36+ leagues, statistical analysis, and custom models—built for people who read the numbers.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen antialiased font-sans text-zinc-50 bg-zinc-900">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
