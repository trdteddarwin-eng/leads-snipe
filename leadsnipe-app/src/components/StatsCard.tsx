'use client';

import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  iconBgColor?: string;
  iconColor?: string;
}

export function StatsCard({
  title,
  value,
  icon: Icon,
  trend,
  iconBgColor = 'bg-blue-50',
  iconColor = 'text-blue-600',
}: StatsCardProps) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-[var(--color-border)] p-6 hover:shadow-md transition-shadow">
      {/* Header with Icon and Trend */}
      <div className="flex items-center justify-between mb-4">
        {/* Icon */}
        <div className={`w-12 h-12 rounded-full ${iconBgColor} flex items-center justify-center`}>
          <Icon className={`w-6 h-6 ${iconColor}`} strokeWidth={2} />
        </div>

        {/* Trend Badge */}
        {trend && (
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
            trend.isPositive
              ? 'bg-green-100 text-green-700'
              : 'bg-red-100 text-red-700'
          }`}>
            {trend.isPositive ? '+' : ''}{trend.value}%
          </span>
        )}
      </div>

      {/* Value */}
      <div className="text-3xl font-bold text-[var(--color-text-primary)] mb-1">
        {value}
      </div>

      {/* Title */}
      <div className="text-sm text-[var(--color-text-secondary)] font-medium">
        {title}
      </div>
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
