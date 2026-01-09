'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Users, Target, TrendingUp, Sparkles } from 'lucide-react';
import { StatsCard, StatsCardSkeleton, HuntTable, HuntTableSkeleton } from '@/components';
import type { Hunt } from '@/lib/types';

export default function Dashboard() {
  const [hunts, setHunts] = useState<Hunt[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalLeads: 0,
    thisWeek: 0,
    avgSuccess: 0,
  });

  useEffect(() => {
    async function fetchData() {
      try {
        const response = await fetch('/api/hunts');
        if (response.ok) {
          const data = await response.json();
          setHunts(data.hunts || []);

          // Calculate stats
          const total = data.hunts?.reduce((acc: number, h: Hunt) => acc + (h.total_leads || 0), 0) || 0;
          const weekAgo = new Date();
          weekAgo.setDate(weekAgo.getDate() - 7);
          const thisWeek = data.hunts?.filter((h: Hunt) => new Date(h.created_at) > weekAgo)
            .reduce((acc: number, h: Hunt) => acc + (h.total_leads || 0), 0) || 0;

          setStats({
            totalLeads: total,
            thisWeek: thisWeek,
            avgSuccess: 73, // Placeholder
          });
        }
      } catch (error) {
        console.error('Failed to fetch hunts:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  const handleDeleteHunt = async (huntId: string) => {
    try {
      const response = await fetch(`/api/hunt/${huntId}`, { method: 'DELETE' });
      if (response.ok) {
        setHunts(hunts.filter(h => h.hunt_id !== huntId));
      }
    } catch (error) {
      console.error('Failed to delete hunt:', error);
    }
  };

  return (
    <div className="max-w-7xl">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)] mb-1">
          Sales Overview
        </h1>
        <p className="text-sm text-[var(--color-text-secondary)]">
          Welcome back, Sarah. Here's what's happening today.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {loading ? (
          <>
            <StatsCardSkeleton />
            <StatsCardSkeleton />
            <StatsCardSkeleton />
            <StatsCardSkeleton />
          </>
        ) : (
          <>
            <StatsCard
              title="Total Leads"
              value={stats.totalLeads.toLocaleString()}
              trend={{ value: 12.5, isPositive: true }}
              icon={Users}
              iconBgColor="bg-blue-50"
              iconColor="text-blue-600"
            />
            <StatsCard
              title="Qualified"
              value={stats.thisWeek.toLocaleString()}
              trend={{ value: 8.2, isPositive: true }}
              icon={Target}
              iconBgColor="bg-purple-50"
              iconColor="text-purple-600"
            />
            <StatsCard
              title="Avg. Score"
              value={stats.avgSuccess}
              trend={{ value: 3.1, isPositive: true }}
              icon={TrendingUp}
              iconBgColor="bg-green-50"
              iconColor="text-green-600"
            />
            <StatsCard
              title="Conversion"
              value="24%"
              trend={{ value: 4.5, isPositive: true }}
              icon={Sparkles}
              iconBgColor="bg-orange-50"
              iconColor="text-orange-600"
            />
          </>
        )}
      </div>

      {/* Recent Hunts Section */}
      <div className="bg-white rounded-2xl shadow-sm border border-[var(--color-border)] p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
            Recent Hunts
          </h2>

          {hunts.length > 0 && (
            <Link
              href="/hunt/new"
              className="text-sm text-[var(--color-brand-blue)] hover:text-[var(--color-brand-blue-dark)] font-medium transition-colors"
            >
              View all →
            </Link>
          )}
        </div>

        {loading ? (
          <HuntTableSkeleton />
        ) : (
          <HuntTable hunts={hunts} onDelete={handleDeleteHunt} />
        )}
      </div>
    </div>
  );
}
