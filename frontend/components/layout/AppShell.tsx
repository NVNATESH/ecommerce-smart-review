"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  BarChart3,
  Boxes,
  Download,
  FileSearch,
  Gauge,
  LayoutDashboard,
  Package,
  Scale,
  ScanSearch,
  ShieldAlert,
  UploadCloud,
} from "lucide-react";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/analysis", label: "Analysis", icon: UploadCloud },
  { href: "/products", label: "My Products", icon: Package },
  { href: "/compare", label: "Compare", icon: Scale },
  { href: "/aspects", label: "Aspect Intelligence", icon: Boxes },
  { href: "/quality", label: "Review Quality", icon: Gauge },
  { href: "/suspicious", label: "Suspicious Reviews", icon: ShieldAlert },
  { href: "/reviews", label: "Review Inspector", icon: FileSearch },
  { href: "/models", label: "Model Performance", icon: BarChart3 },
  { href: "/exports", label: "Exports", icon: Download },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r border-white/5 bg-background-raised/60 backdrop-blur-xl lg:flex">
      <Link href="/" className="flex items-center gap-3 px-6 py-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-accent-blue to-accent-violet shadow-glow">
          <ScanSearch size={18} className="text-white" />
        </div>
        <div className="leading-tight">
          <p className="text-sm font-semibold text-slate-100">Sentiment Engine</p>
          <p className="text-[11px] text-slate-500">Product Intelligence</p>
        </div>
      </Link>
      <nav className="mt-2 flex-1 space-y-1 px-3" aria-label="Dashboard sections">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              className={`group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors ${
                active ? "text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {active && (
                <motion.span
                  layoutId="nav-active"
                  className="absolute inset-0 rounded-xl bg-gradient-to-r from-accent-blue/20 to-accent-violet/10 border border-white/10"
                  transition={{ type: "spring", stiffness: 350, damping: 30 }}
                />
              )}
              <Icon size={17} className={active ? "text-accent-cyan" : "text-slate-500 group-hover:text-slate-300"} />
              <span className="relative">{label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-white/5 px-6 py-4">
        <p className="text-[11px] text-slate-600">
          Explainable NLP · TF-IDF + ML
        </p>
      </div>
    </aside>
  );
}

export function MobileNav() {
  const pathname = usePathname();
  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 flex items-center justify-around border-t border-white/5 bg-background-raised/90 backdrop-blur-xl py-2 lg:hidden">
      {NAV.slice(0, 5).map(({ href, label, icon: Icon }) => {
        const active = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            aria-label={label}
            className={`flex flex-col items-center gap-0.5 p-2 ${active ? "text-accent-cyan" : "text-slate-500"}`}
          >
            <Icon size={18} />
            <span className="text-[9px]">{label.split(" ")[0]}</span>
          </Link>
        );
      })}
    </nav>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <Sidebar />
      <MobileNav />
      <div className="lg:pl-64">
        <main className="mx-auto max-w-7xl px-4 pb-24 pt-6 sm:px-6 lg:pb-10">{children}</main>
      </div>
    </div>
  );
}

export function PageHeader({
  title,
  subtitle,
  right,
}: {
  title: string;
  subtitle?: string;
  right?: React.ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold text-slate-100">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-400">{subtitle}</p>}
      </div>
      {right}
    </div>
  );
}
