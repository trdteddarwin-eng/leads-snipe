'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Target, ChevronRight, Plus, CheckCircle2, Search } from 'lucide-react';
import { api } from '@/lib/api';
import type { Hunt } from '@/lib/types';

export default function Dashboard() {
  const [hunts, setHunts] = useState<Hunt[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('Overview');

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await api.getHunts();
        setHunts(data);
      } catch (error) {
        console.error('Failed to fetch hunts:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const tabs = ['Overview', 'Active_Runs', 'Lead_Feeds'];

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in duration-700">
      {/* Simple Header */}
      <div className="flex justify-between items-end pb-6 border-b border-neutral-100">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900 tracking-tight">
            Lead Generation
          </h1>
          <p className="text-xs text-neutral-400 mt-1 font-medium">
            Monitor your search protocols and extraction performance.
          </p>
        </div>
        <Link href="/hunt/new">
          <button className="h-10 px-6 bg-neutral-900 text-white rounded-xl text-xs font-bold hover:bg-neutral-800 transition-all shadow-lg shadow-neutral-900/10 flex items-center gap-2">
            <Plus className="w-4 h-4" />
            New Hunt
          </button>
        </Link>
      </div>

      {/* Simplified Tabs */}
      <div className="flex items-center gap-8 border-b border-neutral-100">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-4 text-xs font-bold transition-all relative ${activeTab === tab ? 'text-neutral-900' : 'text-neutral-400 hover:text-neutral-600'}`}
          >
            {tab.replace('_', ' ')}
            {activeTab === tab && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-neutral-900 rounded-full" />}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
        {/* Main Content Area */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-black text-neutral-900 uppercase tracking-[0.2em]">Ongoing Protocols</h3>
          </div>

          <div className="space-y-4">
            {loading ? (
              <div className="h-32 bg-white rounded-2xl border border-neutral-100 animate-pulse" />
            ) : hunts.length === 0 ? (
              <div className="p-16 text-center bg-white rounded-3xl border border-dashed border-neutral-200">
                <p className="text-xs font-black text-neutral-400 uppercase tracking-widest">No Active Runs</p>
              </div>
            ) : (
              hunts.slice(0, 3).map(hunt => (
                <div key={hunt.hunt_id} className="bg-white rounded-3xl border border-neutral-100 p-8 flex items-center justify-between shadow-premium hover:scale-[1.01] transition-all group">
                  <div className="flex items-center gap-5">
                    <div className="w-12 h-12 bg-black rounded-2xl flex items-center justify-center text-white shadow-xl shadow-black/10">
                      <Target className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="text-lg font-black text-neutral-900 tracking-tight">{hunt.industry} in {hunt.location}</p>
                      <p className="text-xs text-neutral-500 font-bold uppercase tracking-wider mt-1">{hunt.total_leads || 0} leads discovered</p>
                    </div>
                  </div>
                  <Link href={`/hunt/${hunt.hunt_id}/results`} className="w-10 h-10 rounded-full bg-neutral-50 flex items-center justify-center group-hover:bg-black group-hover:text-white transition-all">
                    <ChevronRight className="w-5 h-5" />
                  </Link>
                </div>
              ))
            )}
          </div>

          <div className="pt-8">
            <h3 className="text-sm font-black text-neutral-900 uppercase tracking-[0.2em] mb-6">Live Discovery Feed</h3>
            <div className="bg-white rounded-[32px] border border-neutral-100 divide-y divide-neutral-50 shadow-premium overflow-hidden">
              {[1, 2, 3].map(i => (
                <div key={i} className="p-6 flex items-center justify-between hover:bg-neutral-50 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50" />
                    <span className="text-sm font-bold text-neutral-900">New Lead Found (B2B SaaS)</span>
                  </div>
                  <span className="text-[10px] font-black text-neutral-400 uppercase">Just Now</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Info Column */}
        <div className="lg:col-span-1 space-y-8">
          <div className="bg-black rounded-[40px] p-10 text-white shadow-2xl shadow-black/20">
            <p className="text-[11px] font-black text-white/40 uppercase tracking-[0.2em] mb-6">System Capacity</p>
            <div className="space-y-8">
              <div>
                <div className="flex justify-between items-end mb-4">
                  <p className="text-5xl font-black tracking-tighter tabular-nums">4,250</p>
                  <p className="text-[10px] font-black text-white/40 uppercase tracking-widest pb-1">Credits</p>
                </div>
                <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                  <div className="w-[85%] h-full bg-white rounded-full shadow-[0_0_15px_rgba(255,255,255,0.5)]" />
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-xs font-black text-neutral-500 uppercase tracking-[0.2em]">Protocol Performance</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white p-6 rounded-[28px] border border-neutral-100 shadow-premium">
                <p className="text-[10px] font-black text-neutral-400 uppercase tracking-wider">Avg Accuracy</p>
                <p className="text-2xl font-black text-neutral-900 mt-2 tracking-tighter">98.4%</p>
              </div>
              <div className="bg-white p-6 rounded-[28px] border border-neutral-100 shadow-premium">
                <p className="text-[10px] font-black text-neutral-400 uppercase tracking-wider">Parallelism</p>
                <p className="text-2xl font-black text-neutral-900 mt-2 tracking-tighter">50x</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
