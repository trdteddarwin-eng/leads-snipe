'use client';

import { Search, Moon, Bell, User } from 'lucide-react';

export function Header() {
  return (
    <header className="h-24 px-12 flex items-center justify-between bg-transparent">
      {/* Search Bar */}
      <div className="w-96">
        <div className="relative group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
          <input
            type="text"
            placeholder="Search..."
            className="w-full pl-12 pr-4 py-3 bg-[#f4f4f4] rounded-xl text-sm border-none focus:outline-none focus:ring-2 focus:ring-black/5 transition-all"
          />
        </div>
      </div>

      {/* User Account */}
      <div className="flex items-center gap-4">
        <div className="text-right hidden sm:block">
          <p className="text-[10px] text-neutral-400 font-medium">Welcome back,</p>
          <p className="text-sm font-bold text-neutral-900">Lauro Morgado</p>
        </div>
        <div className="w-10 h-10 rounded-full overflow-hidden bg-neutral-200 border-2 border-white shadow-soft">
          <img src="https://ui-avatars.com/api/?name=Lauro+Morgado&background=random" alt="User" />
        </div>
      </div>
    </header>
  );
}
