'use client';

import { Search, Moon, Bell, User } from 'lucide-react';

export function Header() {
  return (
    <header className="sticky top-0 z-40 bg-white border-b border-[var(--color-border)] h-16">
      <div className="h-full px-6 flex items-center justify-between">
        {/* Search Bar */}
        <div className="flex-1 max-w-xl">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--color-text-muted)]" />
            <input
              type="text"
              placeholder="Search leads, companies..."
              className="w-full pl-10 pr-4 py-2.5 bg-[var(--color-bg-gray-50)] border border-[var(--color-border)] rounded-lg text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-blue)]/20 focus:border-[var(--color-brand-blue)] transition-all"
            />
          </div>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-3 ml-6">
          {/* Dark Mode Toggle */}
          <button className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-[var(--color-bg-gray-50)] transition-colors">
            <Moon className="w-5 h-5 text-[var(--color-text-secondary)]" />
          </button>

          {/* Notifications */}
          <button className="relative w-9 h-9 flex items-center justify-center rounded-lg hover:bg-[var(--color-bg-gray-50)] transition-colors">
            <Bell className="w-5 h-5 text-[var(--color-text-secondary)]" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>

          {/* User Avatar */}
          <button className="w-9 h-9 flex items-center justify-center rounded-lg bg-[var(--color-brand-blue)] hover:bg-[var(--color-brand-blue-dark)] transition-colors">
            <User className="w-5 h-5 text-white" />
          </button>
        </div>
      </div>
    </header>
  );
}
