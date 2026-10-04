"use client";
import Link from "next/link";
import { ArrowUpRightIcon, CalendarDaysIcon, ChartBarSquareIcon, ClipboardDocumentCheckIcon } from "@heroicons/react/24/outline";
import Navbar from "@/components/Navbar";

const sections = [
  { title: "Fixtures & results", text: "Browse competitions, check kickoff times, and review recorded match results.", href: "/fixtures", icon: CalendarDaysIcon },
  { title: "Predictions & models", text: "Compare market probabilities and inspect the models behind each prediction.", href: "/predictions", icon: ChartBarSquareIcon },
  { title: "Odds & bet journal", text: "Review available South African bookmaker odds and keep track of your selections.", href: "/sa-markets", icon: ClipboardDocumentCheckIcon },
];

export default function LandingPageView() {
  return <div className="min-h-screen bg-zinc-950">
    <Navbar />
    <main id="main-content" className="mx-auto max-w-6xl px-5 sm:px-8">
      <section className="grid gap-12 border-b border-zinc-800 py-16 lg:grid-cols-[1.2fr_1fr] lg:gap-20 lg:py-24">
        <div>
          <p className="mb-6 text-xs font-medium uppercase tracking-[0.18em] text-emerald-300">43v3rB3tz / Football analysis</p>
          <h1 className="max-w-xl text-4xl font-semibold leading-[1.1] tracking-tight sm:text-6xl">Study the match.<br /><span className="text-zinc-500">Understand the numbers.</span></h1>
          <p className="mt-6 max-w-lg text-base leading-7 text-zinc-400">Fixtures, model predictions, bookmaker odds, and results in one workspace. Examine the evidence before choosing a selection.</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/dashboard" className="btn-primary">Open workspace<ArrowUpRightIcon className="h-4 w-4" /></Link>
            <Link href="/register" className="btn-secondary">Create account</Link>
          </div>
          <p className="mt-5 text-xs text-zinc-500">Predictions carry uncertainty. No model guarantees a winning bet.</p>
        </div>
        <div className="self-center rounded-xl border border-zinc-800 bg-zinc-900">
          <div className="border-b border-zinc-800 px-6 py-4 text-sm font-medium">Your match research workflow</div>
          <ol className="divide-y divide-zinc-800">
            {[["Find a fixture", "Choose a league and check the match date."], ["Review the markets", "Compare model estimates with available odds."], ["Measure the outcome", "Check settled results and model performance."]].map(([title, description], index) =>
              <li key={title} className="flex gap-4 px-6 py-6"><span className="pt-0.5 font-mono text-xs text-zinc-500">0{index + 1}</span><div><h2 className="text-sm font-medium">{title}</h2><p className="mt-1.5 text-sm leading-6 text-zinc-400">{description}</p></div></li>)}
          </ol>
          <p className="border-t border-zinc-800 px-6 py-4 text-xs leading-5 text-zinc-500">Availability depends on source coverage and the latest successful sync.</p>
        </div>
      </section>
      <section className="py-12 sm:py-16">
        <div className="mb-8 flex items-baseline justify-between gap-4"><h2 className="text-xl font-semibold tracking-tight">A workspace for the full match cycle</h2><Link href="/pricing" className="shrink-0 text-sm text-zinc-400 hover:text-white">View plans →</Link></div>
        <div className="grid gap-4 md:grid-cols-3">{sections.map(({ title, text, href, icon: Icon }) =>
          <Link key={title} href={href} className="group rounded-xl border border-zinc-800 p-6 transition-colors hover:border-zinc-600 hover:bg-zinc-900">
            <div className="mb-6 flex justify-between"><Icon className="h-6 w-6 text-zinc-400" /><ArrowUpRightIcon className="h-4 w-4 text-zinc-600 group-hover:text-emerald-300" /></div>
            <h3 className="font-medium">{title}</h3><p className="mt-2 text-sm leading-6 text-zinc-400">{text}</p>
          </Link>)}</div>
      </section>
    </main>
    <footer className="border-t border-zinc-800"><div className="mx-auto flex max-w-6xl flex-col gap-2 px-5 py-6 text-xs text-zinc-500 sm:flex-row sm:justify-between sm:px-8"><span>43v3rB3tz © {new Date().getFullYear()}</span><span>Research tools, not betting advice. Bet responsibly.</span></div></footer>
  </div>;
}
