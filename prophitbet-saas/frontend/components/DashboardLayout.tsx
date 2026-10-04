"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-zinc-900">
        <output className="flex items-center gap-3 text-sm text-zinc-400"><span className="animate-spin rounded-full h-5 w-5 border-2 border-zinc-700 border-t-emerald-400" />Loading workspace…</output>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-zinc-900 text-zinc-50">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main id="main-content" className="app-main flex-1 p-4 sm:p-6 lg:p-8 min-w-0">
          <div className="mx-auto w-full max-w-[1440px]">{children}</div>
        </main>
      </div>
    </div>
  );
}
