'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Target, LayoutDashboard, Users, BarChart3, Settings, Zap } from 'lucide-react';

export function Sidebar() {
  const pathname = usePathname();

  const navItems = [
    { name: 'Overview', href: '/', icon: LayoutDashboard },
    { name: 'Leads', href: '/hunt/new', icon: Users },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  const isActive = (href: string) => {
    if (href === '/') {
      return pathname === '/';
    }
    return pathname.startsWith(href);
  };

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-white border-r border-[var(--color-border)] flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-[var(--color-border)]">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--color-brand-blue)] to-purple-600 flex items-center justify-center">
            <Target className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="font-bold text-lg text-[var(--color-text-primary)]">LeadSnipe</div>
            <div className="text-xs text-[var(--color-text-muted)] uppercase tracking-wide">B2B Intelligence</div>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);

            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`
                    flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-all
                    ${active
                      ? 'bg-[var(--color-accent-blue-bg)] text-[var(--color-brand-blue)]'
                      : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-gray-50)] hover:text-[var(--color-text-primary)]'
                    }
                  `}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Upgrade Card */}
      <div className="p-4">
        <div className="bg-gradient-to-br from-[var(--color-brand-blue)] to-purple-600 rounded-2xl p-5 text-white">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="w-5 h-5" />
            <span className="font-semibold text-sm uppercase tracking-wide">Upgrade Plan</span>
          </div>
          <h3 className="font-bold text-lg mb-2">Snipe Premium</h3>
          <p className="text-sm text-white/80 mb-4">Unlock unlimited hunts and advanced features</p>
          <button className="w-full bg-white text-[var(--color-brand-blue)] font-semibold py-2.5 px-4 rounded-lg hover:bg-white/90 transition-colors">
            Get 2x Credits
          </button>
        </div>
      </div>
    </aside>
  );
}
