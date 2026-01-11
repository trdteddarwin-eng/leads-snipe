'use client';

import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon?: LucideIcon;
  variant?: 'blue' | 'pink' | 'white' | 'purple';
  trend?: string;
  trendUp?: boolean;
}

export function StatsCard({
  title,
  value,
  icon: Icon,
  variant = 'white',
  trend,
  trendUp
}: StatsCardProps) {

  const getVariantStyles = () => {
    switch (variant) {
      case 'white':
        return 'bg-white dark:bg-white text-black dark:text-black border-2 border-black dark:border-black';
      default:
        // Use a very light gray or subtle border for variants in B&W mode
        return 'bg-white dark:bg-white text-black dark:text-black border-2 border-black dark:border-black shadow-sm';
    }
  };

  return (
    <div className="p-8 bg-white rounded-[24px] border border-neutral-100 shadow-soft group hover:shadow-premium transition-all duration-500">
      <div className="flex justify-between items-start mb-6">
        <div className="flex flex-col gap-1">
          <span className="text-[10px] font-bold tracking-[0.1em] uppercase text-neutral-400">
            {title}
          </span>
          <h3 className="text-3xl font-bold tracking-tight text-neutral-900">{value}</h3>
        </div>

        {Icon && (
          <div className="w-12 h-12 rounded-2xl bg-neutral-50 flex items-center justify-center group-hover:bg-neutral-900/5 transition-colors">
            <Icon className="w-5 h-5 text-neutral-900" />
          </div>
        )}
      </div>

      {trend && (
        <div className="flex items-center gap-2">
          <div className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${trendUp
            ? 'bg-emerald-50 text-emerald-600'
            : 'bg-neutral-50 text-neutral-500'
            }`}>
            {trend}
          </div>
          <span className="text-[10px] text-neutral-400 font-medium tracking-tight">vs last month</span>
        </div>
      )}
    </div>
  );
}

// Skeleton version for loading state
export function StatsCardSkeleton() {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-[var(--color-border)] p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="w-12 h-12 skeleton rounded-full" />
      </div>
      <div className="space-y-2">
        <div className="h-9 w-24 skeleton" />
        <div className="h-4 w-32 skeleton" />
      </div>
    </div>
  );
}
