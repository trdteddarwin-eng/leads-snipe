'use client';

import { useState } from 'react';
import { Search, ChevronRight, MoreHorizontal, ExternalLink } from 'lucide-react';

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
        <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in duration-700">
            {/* Header */}
            <div className="flex justify-between items-end pb-8 border-b border-neutral-200">
                <div>
                    <h1 className="text-4xl font-black text-neutral-900 tracking-tighter">
                        Lead Database
                    </h1>
                    <p className="text-xs text-neutral-500 mt-2 font-bold uppercase tracking-widest">
                        Total Enriched Entities: <span className="text-neutral-900">{leads.length}</span>
                    </p>
                </div>
                <div className="relative max-w-sm w-full">
                    <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
                    <input
                        type="text"
                        placeholder="Search entities..."
                        className="w-full h-12 bg-white border border-neutral-200 rounded-2xl pl-13 pr-4 text-sm font-bold outline-none focus:border-black focus:ring-4 focus:ring-black/5 transition-all"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
            </div>

            {/* Content Table */}
            <div className="bg-white rounded-[32px] border border-neutral-100 shadow-premium overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-neutral-50/50 text-neutral-900 text-[11px] font-black uppercase tracking-[0.2em] border-b border-neutral-100">
                                <th className="px-10 py-6">Company</th>
                                <th className="px-10 py-6">Contact Details</th>
                                <th className="px-10 py-6">Status</th>
                                <th className="px-10 py-6 text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-neutral-50">
                            {leads.map((lead) => (
                                <tr key={lead.id} className="group hover:bg-neutral-50 transition-colors">
                                    <td className="px-10 py-8">
                                        <div className="text-base font-black text-neutral-900 tracking-tight">{lead.name}</div>
                                        <div className="text-[10px] text-neutral-500 font-black uppercase tracking-widest mt-1">{lead.city}</div>
                                    </td>
                                    <td className="px-10 py-8">
                                        <div className="text-sm font-bold text-neutral-900">{lead.owner}</div>
                                        <div className="text-xs text-neutral-500 font-medium mt-1">{lead.email}</div>
                                    </td>
                                    <td className="px-10 py-8">
                                        <div className="flex items-center gap-3">
                                            <div className={`w-2.5 h-2.5 rounded-full ${lead.status === 'Qualified' ? 'bg-emerald-500 shadow-sm shadow-emerald-500/50' : 'bg-amber-500 shadow-sm shadow-amber-500/50'}`} />
                                            <span className="text-xs font-black text-neutral-900 uppercase tracking-wider">{lead.status}</span>
                                        </div>
                                    </td>
                                    <td className="px-10 py-8 text-right">
                                        <button className="w-10 h-10 rounded-full bg-neutral-50 flex items-center justify-center text-neutral-400 hover:bg-black hover:text-white transition-all">
                                            <ExternalLink className="w-4 h-4" />
                                        </button>
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
