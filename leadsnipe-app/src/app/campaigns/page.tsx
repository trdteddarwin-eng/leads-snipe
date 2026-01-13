'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
    Target,
    ChevronRight,
    Filter,
    Plus,
    MoreHorizontal,
    Calendar,
    Users,
    BarChart3,
    Play,
    Pause,
    AlertCircle
} from 'lucide-react';
import { api } from '@/lib/api';
import type { Hunt } from '@/lib/types';

export default function CampaignsPage() {
    const [hunts, setHunts] = useState<Hunt[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchCampaigns() {
            try {
                const data = await api.getHunts();
                setHunts(data);
            } catch (error) {
                console.error('Failed to fetch campaigns:', error);
            } finally {
                setLoading(false);
            }
        }
        fetchCampaigns();
    }, []);

    return (
        <div className="max-w-7xl mx-auto space-y-10 animate-in fade-in duration-700">
            {/* Breadcrumb */}
            <div className="flex items-center gap-2 text-xs font-bold">
                <span className="text-neutral-400">Platform</span>
                <ChevronRight className="w-3 h-3 text-neutral-300" />
                <span className="text-neutral-900">Campaigns</span>
            </div>

            {/* Header */}
            <div className="flex justify-between items-end pb-8 border-b border-neutral-100">
                <div>
                    <h1 className="text-3xl font-bold text-neutral-900 tracking-tight">
                        Campaigns
                    </h1>
                    <p className="text-xs text-neutral-400 mt-1 font-medium">
                        Manage your active lead generation protocols and extraction runs.
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <button className="h-10 px-5 bg-white border border-neutral-200 rounded-xl text-xs font-bold text-neutral-600 hover:bg-neutral-50 transition-all flex items-center gap-2 shadow-soft">
                        <Filter className="w-3.5 h-3.5" />
                        Filter
                    </button>
                    <Link href="/hunt/new">
                        <button className="h-10 px-6 bg-neutral-900 text-white rounded-xl text-xs font-bold hover:bg-neutral-800 transition-all shadow-lg shadow-neutral-900/10 flex items-center gap-2">
                            <Plus className="w-4 h-4" />
                            New Campaign
                        </button>
                    </Link>
                </div>
            </div>

            {/* Campaigns Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {loading ? (
                    [1, 2, 3].map((i) => (
                        <div key={i} className="h-64 bg-white rounded-[24px] border border-neutral-100 animate-pulse" />
                    ))
                ) : hunts.length === 0 ? (
                    <div className="col-span-full py-20 bg-white rounded-[32px] border border-dashed border-neutral-200 flex flex-col items-center justify-center text-center">
                        <div className="w-16 h-16 bg-neutral-50 rounded-2xl flex items-center justify-center mb-6">
                            <Target className="w-8 h-8 text-neutral-300" />
                        </div>
                        <h3 className="text-lg font-bold text-neutral-900">No active campaigns</h3>
                        <p className="text-xs text-neutral-400 mt-1 max-w-xs font-medium">
                            You haven't initialized any search protocols yet. Start a new hunt to see activity here.
                        </p>
                    </div>
                ) : (
                    hunts.map((hunt) => (
                        <CampaignCard key={hunt.hunt_id} hunt={hunt} />
                    ))
                )}
            </div>
        </div>
    );
}

function CampaignCard({ hunt }: { hunt: Hunt }) {
    const status = hunt.status || 'COMPLETED';

    return (
        <div className="bg-white rounded-[28px] border border-neutral-100 p-6 shadow-soft group hover:border-neutral-200 transition-all h-full flex flex-col">
            <div className="flex justify-between items-start mb-6">
                <div className="w-12 h-12 bg-neutral-50 rounded-2xl flex items-center justify-center border border-neutral-100 group-hover:bg-neutral-900 group-hover:text-white transition-all">
                    <Target className="w-6 h-6" />
                </div>
                <button className="p-2 text-neutral-400 hover:text-neutral-900 transition-colors">
                    <MoreHorizontal className="w-5 h-5" />
                </button>
            </div>

            <div className="flex-1">
                <h3 className="text-lg font-bold text-neutral-900 line-clamp-1">{hunt.industry} in {hunt.location}</h3>
                <p className="text-[11px] text-neutral-400 font-medium mt-1">ID: {hunt.hunt_id.substring(0, 8)}...</p>

                <div className="mt-6 grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                        <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest">Leads Found</p>
                        <p className="text-sm font-bold text-neutral-900">{hunt.total_leads || 0}</p>
                    </div>
                    <div className="space-y-1 text-right">
                        <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest">Target</p>
                        <p className="text-sm font-bold text-neutral-900">{hunt.target || 0}</p>
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="mt-4">
                    <div className="w-full h-1.5 bg-neutral-50 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-neutral-900 rounded-full transition-all"
                            style={{ width: `${Math.min(100, ((hunt.total_leads || 0) / (hunt.target || 1)) * 100)}%` }}
                        />
                    </div>
                </div>
            </div>

            <div className="mt-8 pt-6 border-t border-neutral-50 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${status === 'completed' ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`} />
                    <span className="text-[10px] font-bold uppercase tracking-widest text-neutral-400">{status}</span>
                </div>
                <Link href={`/hunt/${hunt.hunt_id}/results`}>
                    <button className="text-[10px] font-bold text-neutral-900 hover:underline uppercase tracking-widest">
                        View Data
                    </button>
                </Link>
            </div>
        </div>
    );
}
