"use client";

// Authenticated app shell: sidebar navigation + header + auth guard.

import { useEffect, type ReactNode } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth-context";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/ai", label: "AI Briefing", icon: "🤖" },
  { href: "/assistant", label: "AI Assistant", icon: "💬" },
  { href: "/products", label: "Products", icon: "📦" },
  { href: "/sales", label: "Sales", icon: "🧾" },
  { href: "/reports", label: "Reports", icon: "📈" },
  { href: "/insights", label: "Insights", icon: "💡" },
  { href: "/forecast", label: "Forecast", icon: "🔮" },
  { href: "/customers", label: "Customers", icon: "👥" },
  { href: "/categories", label: "Categories", icon: "🏷️" },
  { href: "/suppliers", label: "Suppliers", icon: "🚚" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="flex flex-1 items-center justify-center text-gray-500">
        Loading…
      </div>
    );
  }

  return (
    <div className="flex flex-1">
      <aside className="hidden w-56 shrink-0 flex-col border-r border-gray-200 bg-white p-4 sm:flex dark:border-gray-800 dark:bg-gray-950">
        <div className="mb-6 px-2">
          <p className="text-sm font-semibold text-gray-900 dark:text-white">
            AI Inventory
          </p>
          <p className="text-xs text-gray-400">Management System</p>
        </div>
        <nav className="flex flex-col gap-1">
          {NAV.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${
                  active
                    ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300"
                    : "text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
                }`}
              >
                <span aria-hidden>{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3 dark:border-gray-800 dark:bg-gray-950">
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {user.full_name}
          </div>
          <button
            onClick={logout}
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 transition hover:bg-gray-100 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
          >
            Log out
          </button>
        </header>
        <main className="flex-1 overflow-x-auto p-6">{children}</main>
      </div>
    </div>
  );
}

/** Standard page heading with an optional action slot. */
export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-6 flex items-end justify-between gap-4">
      <div>
        <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
          {title}
        </h1>
        {subtitle && (
          <p className="text-sm text-gray-500 dark:text-gray-400">{subtitle}</p>
        )}
      </div>
      {action}
    </div>
  );
}

/** Primary action button used in page headers. */
export function PrimaryButton({
  children,
  onClick,
}: {
  children: ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-500"
    >
      {children}
    </button>
  );
}
