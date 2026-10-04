"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import * as Dialog from "@radix-ui/react-dialog";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { Bars3Icon, XMarkIcon, ChevronDownIcon } from "@heroicons/react/24/outline";
import { useAuth } from "@/lib/auth";
import { NavigationLinks } from "./Sidebar";
import BackNavigation from "./BackNavigation";

export default function Navbar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  useEffect(() => { setOpen(false); }, [pathname]);
  return (
    <header className="sticky top-0 z-40 border-b border-zinc-800 bg-zinc-950">
      <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6">
        <div className="flex items-center gap-3">
          {user && <Dialog.Root open={open} onOpenChange={setOpen}>
            <Dialog.Trigger asChild><button className="icon-button lg:hidden" aria-label="Open navigation"><Bars3Icon className="h-5 w-5" /></button></Dialog.Trigger>
            <Dialog.Portal>
              <Dialog.Overlay className="fixed inset-0 z-50 bg-black/65" />
              <Dialog.Content className="fixed inset-y-0 left-0 z-50 flex w-80 max-w-[90vw] flex-col border-r border-zinc-800 bg-zinc-950 shadow-xl">
                <div className="flex h-16 shrink-0 items-center justify-between border-b border-zinc-800 px-5">
                  <Dialog.Title className="font-semibold">43v3rB3tz</Dialog.Title>
                  <Dialog.Close asChild><button className="icon-button" aria-label="Close navigation"><XMarkIcon className="h-5 w-5" /></button></Dialog.Close>
                </div>
                <Dialog.Description className="sr-only">Navigate your football analysis workspace.</Dialog.Description>
                <div className="overflow-y-auto p-3"><NavigationLinks onNavigate={() => setOpen(false)} /></div>
              </Dialog.Content>
            </Dialog.Portal>
          </Dialog.Root>}
          <Link href={user ? "/dashboard" : "/"} className="flex items-center gap-2.5 font-semibold tracking-tight">
            <span aria-hidden="true" className="flex h-8 w-8 items-center justify-center rounded-lg border border-emerald-400/30 bg-emerald-400/10 text-sm text-emerald-300">43</span>
            <span>43v3rB3tz</span>
          </Link>
          <span className="hidden border-l border-zinc-800 pl-4 text-xs text-zinc-500 md:block">Football workspace</span>
        </div>
        <div className="flex items-center gap-2 sm:gap-4">
          <div className="hidden sm:block"><BackNavigation /></div>
          {user ? <DropdownMenu.Root>
            <DropdownMenu.Trigger asChild><button className="flex min-h-10 items-center gap-2 rounded-lg border border-zinc-800 px-3 text-sm text-zinc-300 hover:bg-zinc-900" aria-label="Account menu">
              <span className="max-w-36 truncate">{user.name || "Account"}</span><ChevronDownIcon className="h-4 w-4" />
            </button></DropdownMenu.Trigger>
            <DropdownMenu.Portal><DropdownMenu.Content align="end" sideOffset={8} className="z-[60] w-64 rounded-lg border border-zinc-700 bg-zinc-900 p-1.5 shadow-xl">
              <DropdownMenu.Label className="px-2 py-2 text-xs text-zinc-400"><span className="block truncate">{user.email}</span><span className="mt-1 block capitalize">{user.plan} plan</span></DropdownMenu.Label>
              <DropdownMenu.Separator className="my-1 h-px bg-zinc-800" />
              <DropdownMenu.Item asChild><Link className="menu-item" href="/settings">Account settings</Link></DropdownMenu.Item>
              <DropdownMenu.Item asChild><Link className="menu-item" href="/billing">Billing</Link></DropdownMenu.Item>
              <DropdownMenu.Separator className="my-1 h-px bg-zinc-800" />
              <DropdownMenu.Item className="menu-item text-red-300" onSelect={() => { void logout(); }}>Sign out</DropdownMenu.Item>
            </DropdownMenu.Content></DropdownMenu.Portal>
          </DropdownMenu.Root> : <>
            <Link href="/pricing" className="hidden text-sm text-zinc-400 hover:text-white sm:block">Pricing</Link>
            <Link href="/login" className="btn-secondary !px-3">Sign in</Link>
          </>}
        </div>
      </div>
      <div className="border-t border-zinc-800 px-3 sm:hidden"><BackNavigation /></div>
    </header>
  );
}
