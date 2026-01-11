'use client';

import { useState } from 'react';
import {
    Users,
    Search,
    Plus,
    MoreVertical,
    Building2,
    Globe,
    Mail,
    Phone,
    CheckCircle2,
    ExternalLink
} from 'lucide-react';

export default function LeadsPage() {
    const [searchQuery, setSearchQuery] = useState('');

    const leads = [
        { id: 1, name: 'Crystal Dental', owner: 'Sarah Johnson', email: 'sarah@crystaldental.com', city: 'Miami, FL', status: 'Qualified' },
        { id: 2, name: 'Blue Sky HVAC', owner: 'Mike Miller', email: 'mike@blueskyhvac.net', city: 'Austin, TX', status: 'In Outreach' },
        { id: 3, name: 'Precision Plumbers', owner: 'Robert Chen', email: 'robert@precision.io', city: 'Seattle, WA', status: 'New' },
        { id: 4, name: 'Urban Real Estate', owner: 'Elena Gomez', email: 'elena@urbanre.com', city: 'Miami, FL', status: 'Qualified' },
        { id: 5, name: 'Advanced Ortho', owner: 'David Park', email: 'dpark@advortho.md', city: 'Toronto, ON', status: 'Qualified' },
    ];

    return (
        <div className="p-8 max-w-7xl mx-auto space-y-12 animate-fade-in">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b-[3px] border-black dark:border-black pb-8">
                <div>
                    <h1 className="text-4xl font-black uppercase tracking-tighter text-black dark:text-black">Database_Leads</h1>
                    <p className="text-xs font-bold text-neutral-400 uppercase tracking-widest mt-2 font-mono">Total_Enriched_Entities: {leads.length}</p>
                </div>
                <button className="bg-black dark:bg-black text-white dark:text-white font-black py-4 px-8 text-xs uppercase tracking-[0.2em] hover:opacity-80 transition-all font-mono">
                    Snipe_New
                </button>
            </div>

            {/* Filters & Search */}
            <div className="grid grid-cols-1 md:grid-cols-[1fr_200px] gap-0 border-[2px] border-black dark:border-black">
                <div className="relative">
                    <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
                    <input
                        type="text"
                        placeholder="SEARCH_BY_QUERY"
                        className="w-full pl-16 pr-6 py-6 bg-transparent border-none focus:ring-0 text-sm font-bold placeholder:text-neutral-300 uppercase font-mono text-black dark:text-black"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
                <button className="bg-white dark:bg-white text-black dark:text-black font-black text-[10px] uppercase tracking-widest border-l-[2px] border-black dark:border-black font-mono">
                    Filter:_All
                </button>
            </div>

            {/* Leads Table */}
            <div className="border-[2px] border-black dark:border-black overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-white dark:bg-white text-black dark:text-black border-b-2 border-black dark:border-black">
                                <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest font-mono">01_Entity</th>
                                <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest font-mono">02_Protocol</th>
                                <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest font-mono">03_Sector</th>
                                <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest font-mono">04_Status</th>
                                <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest font-mono text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y-2 divide-neutral-100 dark:divide-neutral-100">
                            {leads.map((lead) => (
                                <tr key={lead.id} className="group hover:bg-neutral-50 dark:hover:bg-neutral-50 transition-colors">
                                    <td className="px-6 py-8">
                                        <div className="font-black text-sm uppercase text-black dark:text-black">{lead.name}</div>
                                        <div className="text-[10px] text-neutral-400 font-bold uppercase tracking-tight mt-1 font-mono">LOC: {lead.city}</div>
                                    </td>
                                    <td className="px-6 py-8">
                                        <div className="space-y-1">
                                            <div className="text-xs font-black uppercase text-black dark:text-black">{lead.owner}</div>
                                            <div className="text-[10px] text-neutral-400 font-bold font-mono">{lead.email}</div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-8">
                                        <div className="text-[10px] font-black uppercase text-neutral-500 font-mono">B2B_SECTOR</div>
                                    </td>
                                    <td className="px-6 py-8">
                                        <span className={`px-2 py-1 text-[9px] font-black uppercase tracking-tighter font-mono ${lead.status === 'Qualified' ? 'bg-black text-white dark:bg-black dark:text-white' :
                                            'border border-black dark:border-black text-black dark:text-black'
                                            }`}>
                                            {lead.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-8 text-right">
                                        <div className="flex items-center justify-end gap-2">
                                            <button className="p-2 border border-transparent hover:border-black dark:hover:border-black transition-all">
                                                <ExternalLink className="w-4 h-4" />
                                            </button>
                                            <button className="p-2 border border-transparent hover:border-black dark:hover:border-black transition-all">
                                                <MoreVertical className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
