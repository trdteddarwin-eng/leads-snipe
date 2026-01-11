'use client';

import { Search } from 'lucide-react';

export function Header() {
  return (
    <header className="h-20 px-8 flex items-center justify-between bg-transparent">
      {/* Search Bar - Simplified */}
      <div className="flex-1 max-w-xl">
        <div className="relative group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-300 group-focus-within:text-neutral-900 transition-colors" />
          <input
            type="text"
            placeholder="Search leads or campaigns..."
            className="w-full h-10 bg-white border border-neutral-100 rounded-full pl-11 pr-4 text-sm font-medium outline-none focus:border-neutral-200 focus:ring-4 focus:ring-neutral-900/5 transition-all placeholder:text-neutral-300"
          />
        </div>
      </div>

      {/* Simplified User Account */}
      <div className="flex items-center gap-3 ml-6">
        <div className="text-right hidden sm:block">
          <p className="text-sm font-bold text-neutral-900">Lauro Morgado</p>
        </div>
        <div className="w-9 h-9 rounded-full bg-neutral-900 flex items-center justify-center text-white text-xs font-bold border-2 border-white shadow-soft">
          LM
        </div>
      </div>
    </header>
  );
}
