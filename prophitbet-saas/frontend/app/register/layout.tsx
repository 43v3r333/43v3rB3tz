import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Create Account — 43v3r Bets",
  description: "Create a free 43v3r Bets account and start getting AI-powered soccer predictions in minutes.",
};

export default function RegisterLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
