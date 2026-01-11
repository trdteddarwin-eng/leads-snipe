'use client';

import {
    BarChart3,
    TrendingUp,
    Users,
    Target,
    ArrowUpRight,
    ArrowDownRight,
    Filter,
    Download,
    Sparkles,
    Calendar
} from 'lucide-react';
import { StatsCard } from '@/components';

export default function AnalyticsPage() {
    const stats = [
        { name: 'Total Opportunities', value: '45,231', change: '+12.5%', trend: 'up' },
        { name: 'Avg. Qualification', value: '24.8%', change: '+4.2%', trend: 'up' },
        { name: 'Owner Found', value: '89.2%', change: '-0.8%', trend: 'down' },
        { name: 'Response Rate', value: '18.4%', change: '+2.1%', trend: 'up' },
    ];

    return (
        <div className="max-w-7xl mx-auto space-y-12 animate-in fade-in duration-700">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-end gap-6">
                <div>
                    <h1 className="text-[32px] font-bold text-neutral-900 tracking-tight leading-tight">
                        Analytics
                    </h1>
                    <p className="text-neutral-500 text-sm mt-1 font-medium">
                        Detailed performance metrics and global pipeline analysis.
                    </p>
                </div>
                <div className="flex gap-3">
                    <button className="flex items-center gap-2 px-6 py-3.5 bg-white border border-neutral-100 rounded-2xl text-xs font-bold text-neutral-600 hover:bg-neutral-50 transition-all shadow-soft">
                        <Filter className="w-4 h-4" />
                        <span>Filters</span>
                    </button>
                    <button className="flex items-center gap-2 px-6 py-3.5 bg-neutral-900 rounded-2xl text-xs font-bold text-white hover:bg-neutral-800 transition-all shadow-lg shadow-neutral-900/10">
                        <Download className="w-4 h-4" />
                        <span>Export Data</span>
                    </button>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {stats.map((stat) => (
                    <StatsCard
                        key={stat.name}
                        title={stat.name}
                        value={stat.value}
                        trend={stat.change}
                        trendUp={stat.trend === 'up'}
                        icon={stat.name.includes('Opportunities') ? Target : stat.name.includes('Rate') ? Sparkles : BarChart3}
                    />
                ))}
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="p-10 bg-white rounded-[32px] border border-neutral-100 shadow-soft min-h-[500px] flex flex-col">
                    <div className="mb-10 flex justify-between items-start">
                        <div>
                            <h3 className="text-xl font-bold text-neutral-900 tracking-tight">Acquisition Trend</h3>
                            <div className="flex items-center gap-2 text-xs text-neutral-400 font-medium mt-1">
                                <Calendar className="w-3.5 h-3.5" />
                                <span>Rolling 30-Day Cycle</span>
                            </div>
                        </div>
                        <div className="px-3 py-1 bg-neutral-50 rounded-lg text-[10px] font-bold text-neutral-500">
                            LIVE
                        </div>
                    </div>

                    {/* Placeholder Chart Area */}
                    <div className="flex-1 w-full bg-neutral-50/50 rounded-[24px] flex flex-col items-center justify-center border border-dashed border-neutral-100 group">
                        <div className="w-16 h-16 rounded-full bg-white flex items-center justify-center shadow-soft mb-6 group-hover:scale-110 transition-transform">
                            <BarChart3 className="w-8 h-8 text-neutral-200" />
                        </div>
                        <p className="text-xs font-bold text-neutral-300 uppercase tracking-widest">Generating Visual Data...</p>
                    </div>
                </div>

                <div className="p-10 bg-white rounded-[32px] border border-neutral-100 shadow-soft min-h-[500px] flex flex-col">
                    <div className="mb-10 flex justify-between items-start">
                        <div>
                            <h3 className="text-xl font-bold text-neutral-900 tracking-tight">Sector Distribution</h3>
                            <div className="flex items-center gap-2 text-xs text-neutral-400 font-medium mt-1">
                                <Users className="w-3.5 h-3.5" />
                                <span>Vertical Industry Breakdown</span>
                            </div>
                        </div>
                    </div>

                    <div className="space-y-10 flex-1">
                        {[
                            { name: 'Dentists', val: 45, color: 'bg-neutral-900' },
                            { name: 'Plumbers', val: 32, color: 'bg-neutral-600' },
                            { name: 'HVAC', val: 18, color: 'bg-neutral-400' },
                            { name: 'Real Estate', val: 5, color: 'bg-neutral-200' }
                        ].map(industry => (
                            <div key={industry.name} className="space-y-4">
                                <div className="flex justify-between items-end">
                                    <span className="text-sm font-bold text-neutral-900">{industry.name}</span>
                                    <span className="text-xs font-bold text-neutral-400">{industry.val}%</span>
                                </div>
                                <div className="w-full h-3 bg-neutral-50 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full ${industry.color} rounded-full transition-all duration-1000 ease-out`}
                                        style={{ width: `${industry.val}%` }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
