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

      {/* Balance Card */}
      <div className="px-6 mb-8">
        <div className="bg-[#2a2a2b] p-6 rounded-[24px] border border-white/10 shadow-xl shadow-black/20">
          <p className="text-[10px] text-white/40 font-black mb-2 tracking-[0.2em] uppercase text-center">Available Credits</p>
          <div className="flex items-center justify-center gap-2">
            <span className="text-white font-black text-3xl tabular-nums tracking-tighter">4,250</span>
          </div>
        </div>
      </div>

      {/* Core Navigation */}
      <div className="flex-1 overflow-y-auto px-4 space-y-2">
        <NavItem href="/" icon={LayoutDashboard} label="Dashboard" active={isActive('/')} />
        <NavItem href="/leads" icon={Users} label="Lead Database" active={isActive('/leads')} />
        <NavItem href="/campaigns" icon={Target} label="Campaigns" active={isActive('/campaigns')} />
        <NavItem href="/analytics" icon={BarChart3} label="Analytics" active={isActive('/analytics')} />
        <div className="pt-4 mt-6 border-t border-white/10">
          <NavItem href="/settings" icon={Settings} label="Settings" active={isActive('/settings')} />
        </div>
      </div>

      {/* Footer Profile */}
      <div className="p-6">
        <div className="flex items-center gap-3 px-2">
          <div className="w-8 h-8 rounded-full overflow-hidden border border-white/10">
            <img src="https://ui-avatars.com/api/?name=Lauro+Morgado&background=random" alt="User" />
          </div>
          <p className="text-xs font-bold text-white/80 truncate">Lauro Morgado</p>
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
        flex items-center gap-4 px-5 py-4 rounded-[16px] text-sm font-bold transition-all duration-200 group
        ${active
          ? 'bg-white text-black shadow-lg shadow-white/5'
          : 'text-white/60 hover:text-white hover:bg-white/5'
        }
      `}
    >
      <Icon className={`w-5 h-5 ${active ? 'text-black' : 'text-white/40 group-hover:text-white'}`} />
      <span>{label}</span>
      {active && <div className="ml-auto w-1.5 h-1.5 bg-black rounded-full" />}
    </Link>
  );
}
