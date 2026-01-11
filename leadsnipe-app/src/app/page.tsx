'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Users, Target, TrendingUp, Sparkles, Trash2, Calendar, MapPin } from 'lucide-react';
import { StatsCard, StatsCardSkeleton, HuntTable, HuntTableSkeleton } from '@/components';
import type { Hunt } from '@/lib/types';
import { api } from '@/lib/api';

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
        const data = await api.getHunts();
        setHunts(data);

        // Calculate stats
        const total = data.reduce((acc: number, h: Hunt) => acc + (h.total_leads || 0), 0) || 0;
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        const thisWeek = data.filter((h: Hunt) => new Date(h.created_at) > weekAgo)
          .reduce((acc: number, h: Hunt) => acc + (h.total_leads || 0), 0) || 0;

        setStats({
          totalLeads: total,
          thisWeek: thisWeek,
          avgSuccess: 73, // Placeholder
        });
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
    <div className="max-w-7xl mx-auto space-y-12 animate-in fade-in duration-700">
      {/* Dashboard Top Header */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-[32px] font-bold text-neutral-900 tracking-tight leading-tight">
            Dashboard
          </h1>
          <p className="text-neutral-500 text-sm mt-1 font-medium">
            Monitor your lead generation activity and campaign ROI in real-time.
          </p>
        </div>
        <Link href="/hunt/new">
          <button className="bg-neutral-900 text-white px-8 py-4 rounded-full text-sm font-bold hover:bg-neutral-800 transition-all shadow-lg shadow-neutral-900/10 active:scale-95 flex items-center gap-2">
            <Target className="w-4 h-4" />
            Initiate new hunt
          </button>
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <>
            <StatsCardSkeleton />
            <StatsCardSkeleton />
            <StatsCardSkeleton />
          </>
        ) : (
          <>
            <StatsCard
              title="Pipeline Yield"
              value={`${stats.totalLeads.toLocaleString()}`}
              icon={TrendingUp}
              trend="+28%"
              trendUp={true}
            />
            <StatsCard
              title="Qualified Leads"
              value={stats.thisWeek.toLocaleString()}
              icon={Target}
              trend="+15%"
              trendUp={true}
            />
            <StatsCard
              title="Success Rate"
              value="73.4%"
              icon={Sparkles}
              trend="+2.4%"
              trendUp={true}
            />
          </>
        )}
      </div>

      {/* Active Campaign Hero - Styled like the reference image "Active Booking" */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-neutral-900">Active Hunting</h2>
          <Link href="/campaigns" className="text-xs font-bold text-neutral-400 hover:text-neutral-900 transition-colors flex items-center gap-2">
            Go to archive
            <div className="w-5 h-5 rounded-full bg-neutral-100 flex items-center justify-center text-[8px]">→</div>
          </Link>
        </div>

        <div className="bg-white rounded-[32px] border border-neutral-100 shadow-soft overflow-hidden">
          <div className="p-10 flex flex-col lg:flex-row gap-12">
            {/* Left: Campaign Visualization */}
            <div className="lg:w-1/2 relative bg-neutral-50 rounded-[28px] p-8 flex items-center justify-center min-h-[340px]">
              <div className="absolute top-6 left-6 bg-white px-3 py-1.5 rounded-lg shadow-sm flex items-center gap-2 border border-neutral-100">
                <Target className="w-4 h-4 text-neutral-900" />
                <span className="text-[10px] font-bold uppercase tracking-wider">SNIPE_CORE</span>
              </div>

              {/* Abstract Visual (Simulating the car image) */}
              <div className="flex items-end gap-3 h-48">
                {[40, 70, 45, 90, 65, 85, 50].map((h, i) => (
                  <div
                    key={i}
                    className="w-10 bg-neutral-900 rounded-xl"
                    style={{ height: `${h}%`, opacity: 0.05 + (i * 0.1) }}
                  />
                ))}
              </div>
            </div>

            {/* Right: Campaign Details */}
            <div className="lg:w-1/2 flex flex-col justify-between py-2">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-2xl font-bold text-neutral-900 mb-1">B2B SaaS Outreach (High Priority)</h3>
                  <div className="flex items-center gap-2 text-xs text-neutral-400 font-medium tracking-tight">
                    <Calendar className="w-3 h-3" />
                    <span>Started 03.02.22</span>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-4xl font-bold text-neutral-900">$1,250</span>
                  <p className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider mt-1">Estimated ROI</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-y-8 gap-x-12 mt-12">
                <DetailRow label="Target Sector" value="Fintech / SaaS" />
                <DetailRow label="Location" value="US, UK, Germany" />
                <DetailRow label="Leads Found" value="1,240 / 5,000" />
                <DetailRow label="Accuracy" value="98.4%" />
              </div>

              <div className="flex items-center gap-4 mt-12">
                <button className="w-12 h-12 rounded-full border border-neutral-100 flex items-center justify-center text-neutral-400 hover:bg-neutral-50 hover:text-neutral-900 transition-all">
                  <Sparkles className="w-5 h-5" />
                </button>
                <button className="w-12 h-12 rounded-full border border-neutral-100 flex items-center justify-center text-neutral-400 hover:bg-neutral-50 hover:text-neutral-900 transition-all">
                  <TrendingUp className="w-5 h-5" />
                </button>
                <button className="w-12 h-12 rounded-full border border-neutral-100 flex items-center justify-center text-neutral-400 hover:bg-neutral-50 hover:text-rose-500 transition-all ml-auto">
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Bottom Stats Grid (Horizontal like the reference image) */}
          <div className="bg-neutral-50/50 border-t border-neutral-100 grid grid-cols-2 md:grid-cols-4 divide-x divide-neutral-100">
            <BottomStat label="Source" value="LinkedIn, Apollo" />
            <BottomStat label="Extraction" value="Parallel_JS" />
            <BottomStat label="Validation" value="Active_SMTP" />
            <BottomStat label="Concurrency" value="50 Streams" />
          </div>
        </div>
      </div>

      {/* Activity Logs / Table */}
      <div className="space-y-6">
        <div className="flex items-center justify-between px-2">
          <div className="space-y-1">
            <h2 className="text-xl font-bold text-neutral-900 tracking-tight">
              Operational History
            </h2>
            <p className="text-xs text-neutral-400 font-medium">
              Check all previous scraping runs and exported datasets.
            </p>
          </div>
        </div>

        {hunts.length === 0 && !loading ? (
          <div className="p-16 flex flex-col items-center justify-center text-center bg-white rounded-[32px] border border-neutral-100">
            <div className="w-20 h-20 bg-neutral-50 rounded-2xl flex items-center justify-center mb-8">
              <Target className="w-8 h-8 text-neutral-400" />
            </div>
            <h3 className="text-xl font-bold text-neutral-900 tracking-tight mb-2">No active protocols</h3>
            <p className="text-sm text-neutral-400 max-w-sm mx-auto mb-10 font-medium">
              Start your first lead generation campaign to see data here.
            </p>
            <button className="bg-neutral-900 text-white px-10 py-4 rounded-full font-bold text-sm hover:bg-neutral-800 transition-all shadow-lg shadow-neutral-900/10 active:scale-95">
              Initialize Sequence
            </button>
          </div>
        ) : loading ? (
          <HuntTableSkeleton />
        ) : (
          <HuntTable hunts={hunts} onDelete={handleDeleteHunt} />
        )}
      </div>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest mb-1.5">{label}</p>
      <p className="text-sm font-bold text-neutral-900">{value}</p>
    </div>
  );
}

function BottomStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="px-8 py-5">
      <p className="text-[9px] font-bold text-neutral-400 uppercase tracking-widest mb-1">{label}</p>
      <p className="text-xs font-bold text-neutral-900">{value}</p>
    </div>
  );
}
