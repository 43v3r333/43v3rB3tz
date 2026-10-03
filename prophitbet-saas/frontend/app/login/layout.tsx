import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign In — 43v3r Bets",
  description: "Sign in to your 43v3r Bets account to access AI soccer predictions and analysis tools.",
};

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
