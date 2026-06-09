'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Leaf, Activity, Trophy, Settings } from 'lucide-react';

/**
 * Navigation link definitions for the dashboard sidebar.
 * Add or remove entries here to change the nav structure.
 */
const NAV_LINKS = [
  { href: '/dashboard', label: 'Overview', Icon: Activity },
  { href: '/dashboard/twin', label: 'Carbon Twin', Icon: Leaf },
  { href: '/dashboard/community', label: 'Community', Icon: Trophy },
] as const;

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-zinc-950 text-gray-900 dark:text-zinc-50">
      {/* ── Sidebar Navigation ───────────────────────────────────────────── */}
      <nav
        aria-label="Main navigation"
        className="w-64 border-r border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-4 hidden md:flex flex-col"
      >
        {/* Logo / Brand */}
        <div className="flex items-center gap-2 mb-8 px-2" aria-label="EcoTrace AI+ home">
          <Leaf className="text-green-500 h-8 w-8" aria-hidden="true" />
          <span className="text-xl font-bold bg-gradient-to-r from-green-500 to-emerald-600 bg-clip-text text-transparent">
            EcoTrace AI+
          </span>
        </div>

        {/* Primary nav links */}
        <ul role="list" className="space-y-1 flex-1">
          {NAV_LINKS.map(({ href, label, Icon }) => {
            const isActive = pathname === href;
            return (
              <li key={href}>
                <Link
                  href={href}
                  aria-current={isActive ? 'page' : undefined}
                  className={[
                    'flex items-center gap-3 px-3 py-2 rounded-lg transition-colors font-medium',
                    'outline-none focus-visible:ring-2 focus-visible:ring-green-500 focus-visible:ring-offset-2',
                    isActive
                      ? 'bg-green-50 text-green-700 dark:bg-green-950/60 dark:text-green-300'
                      : 'hover:bg-gray-100 dark:hover:bg-zinc-800 text-gray-700 dark:text-zinc-300',
                  ].join(' ')}
                >
                  <Icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                  <span>{label}</span>
                </Link>
              </li>
            );
          })}
        </ul>

        {/* Settings link at bottom */}
        <div className="border-t border-gray-200 dark:border-zinc-800 pt-4 mt-auto">
          <Link
            href="/settings"
            aria-label="Application settings"
            className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors font-medium text-gray-500 dark:text-gray-400 outline-none focus-visible:ring-2 focus-visible:ring-green-500 focus-visible:ring-offset-2"
          >
            <Settings className="h-5 w-5 shrink-0" aria-hidden="true" />
            <span>Settings</span>
          </Link>
        </div>
      </nav>

      {/* ── Main Content ──────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Skip-to-content link — only visible when focused via keyboard */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-green-600 text-white px-4 py-2 rounded-lg z-50 font-medium"
        >
          Skip to main content
        </a>

        <main
          id="main-content"
          className="flex-1 overflow-y-auto"
          tabIndex={-1}
        >
          <div className="p-8 max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
