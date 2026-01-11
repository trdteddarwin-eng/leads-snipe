'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Target, LayoutDashboard, Users, BarChart3, Settings } from 'lucide-react';

export function Sidebar() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === '/') {
      return pathname === '/';
    }
    return pathname.startsWith(href);
  };

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-[var(--color-bg-sidebar)] flex flex-col z-50 overflow-hidden">
      {/* Brand Logo */}
      <div className="h-24 flex items-center px-8">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-white/10 rounded flex items-center justify-center">
            <Target className="w-4 h-4 text-white" />
          </div>
          <span className="text-white font-bold tracking-tight text-xl italic">lead<span className="opacity-60">snipe</span></span>
        </div>
      </div>

      {/* Balance Card - LEADSNIPE VERSION */}
      <div className="px-6 mb-8">
        <div className="bg-[#2a2a2b] p-5 rounded-[20px] border border-white/5">
          <p className="text-[10px] text-white/40 font-medium mb-1 tracking-wider uppercase">Lead Credits</p>
          <div className="flex items-baseline gap-1">
            <span className="text-white font-bold text-2xl">4,250</span>
            <span className="text-white/20 text-sm">/ mo</span>
          </div>
        </div>
      </div>

      {/* Navigation Groups */}
      <div className="flex-1 overflow-y-auto px-4 space-y-8">
        {/* MENU Group */}
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-white/20 px-4 mb-4">Menu</p>
          <div className="space-y-1">
            <NavItem href="/" icon={LayoutDashboard} label="Dashboard" active={isActive('/')} />
            <NavItem href="/leads" icon={Users} label="Leads" active={isActive('/leads')} />
            <NavItem href="/campaigns" icon={Target} label="Campaigns" active={isActive('/campaigns')} />
            <NavItem href="/analytics" icon={BarChart3} label="Analytics" active={isActive('/analytics')} />
          </div>
        </div>

        {/* OTHER Group */}
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-white/20 px-4 mb-4">Other</p>
          <div className="space-y-1">
            <NavItem href="/settings" icon={Settings} label="Settings" active={isActive('/settings')} />
            <NavItem href="/support" icon={Target} label="Support" active={isActive('/support')} />
          </div>
        </div>
      </div>

      {/* Footer Profile - Minimal like the image but keeping current info */}
      <div className="p-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full overflow-hidden bg-slate-700">
            <img src="https://ui-avatars.com/api/?name=Lauro+Morgado&background=random" alt="User" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-white truncate">Lauro Morgado</p>
            <p className="text-[10px] text-white/30 truncate">Welcome back!</p>
          </div>
        </div>
      </div>
    </aside>
  );
}

function NavItem({ href, icon: Icon, label, active }: { href: string; icon: any; label: string; active: boolean }) {
  return (
    <Link
      href={href}
      className={`
        flex items-center gap-3 px-4 py-3 rounded-[12px] text-xs font-medium transition-all duration-200 group
        ${active
          ? 'bg-[var(--color-bg-sidebar-active)] text-white'
          : 'text-white/40 hover:text-white hover:bg-white/5'
        }
      `}
    >
      <Icon className={`w-4 h-4 ${active ? 'text-white' : 'text-white/30 group-hover:text-white'}`} />
      <span>{label}</span>
      {active && <div className="ml-auto w-1 h-4 bg-white rounded-full" />}
    </Link>
  );
}
