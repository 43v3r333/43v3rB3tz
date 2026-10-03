import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pricing — 43v3r Bets",
  description: "Simple, transparent pricing for AI soccer predictions. Start free, upgrade when you need more power.",
  openGraph: {
    title: "43v3r Bets Pricing",
    description: "AI soccer predictions from $0/month. Free, Pro, and Elite plans available.",
  },
};

export default function PricingLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
