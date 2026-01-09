'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';

export default function LeadsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('All');

  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchLeads() {
      try {
        const data = await api.getLeads();
        // The API returns { leads: [...], total: n }
        setLeads(data.leads || []);
      } catch (err) {
        console.error('Failed to fetch leads:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchLeads();
  }, []);

  const filters = ['All', 'New', 'Contacted', 'Replied', 'Meeting Booked'];

  const getStatusColor = (status: string) => {
    const colors = {
      new: 'bg-blue-100 text-blue-800',
      contacted: 'bg-yellow-100 text-yellow-800',
      replied: 'bg-green-100 text-green-800',
      meeting_booked: 'bg-purple-100 text-purple-800',
    };
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const getStatusLabel = (status: string) => {
    const labels = {
      new: 'New',
      contacted: 'Contacted',
      replied: 'Replied',
      meeting_booked: 'Meeting Booked',
    };
    return labels[status as keyof typeof labels] || status;
  };

  return (
    <div className="min-h-screen bg-background-light">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-primary">All Leads</h1>
              <p className="text-sm text-gray-600 font-medium">{leads.length} total</p>
            </div>
            <Link href="/dashboard" className="text-brand-blue hover:text-blue-700 font-semibold transition-colors">
              ← Back to Dashboard
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search and Filters */}
        <div className="mb-6">
          <div className="flex gap-4 mb-4">
            <div className="flex-1 relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xl">🔍</span>
              <input
                type="text"
                className="input-field pl-12"
                placeholder="Search by name or company..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>

          <div className="flex gap-2 flex-wrap">
            {filters.map((filter) => (
              <button
                key={filter}
                onClick={() => setSelectedFilter(filter)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 ${selectedFilter === filter
                    ? 'bg-brand-blue text-white shadow-md'
                    : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 hover:border-brand-blue'
                  }`}
              >
                {filter}
              </button>
            ))}
          </div>
        </div>

        {/* Leads Grid */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-12 h-12 border-4 border-brand-blue border-t-transparent rounded-full animate-spin mb-4" />
            <p className="text-gray-500 font-medium">Fetching your leads...</p>
          </div>
        ) : leads.length === 0 ? (
          <div className="text-center py-20 card bg-gray-50 border-dashed border-2">
            <p className="text-3xl mb-4">🔦</p>
            <h3 className="text-xl font-bold text-primary mb-2">No leads found</h3>
            <p className="text-gray-500 mb-6">You haven't generated any leads yet.</p>
            <Link href="/campaigns/new" className="btn-primary inline-flex items-center px-8">
              Start a Hunt
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {leads.map((lead) => (
              <Link
                key={lead.id}
                href={`/leads/${lead.id}`}
                className="card hover:shadow-xl hover:scale-[1.02] transition-all duration-200 group"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-primary mb-1 group-hover:text-brand-blue transition-colors">
                      {lead.name}
                    </h3>
                    <p className="text-gray-600 font-medium">
                      {lead.owner_name ? `${lead.owner_name} · Owner` : 'Decision Maker'}
                    </p>
                  </div>
                  <button className="text-2xl hover:scale-110 transition-transform">
                    {lead.isFavorite ? '⭐' : '☆'}
                  </button>
                </div>

                <div className="space-y-2.5 mb-4">
                  <div className="flex items-center text-sm text-gray-600">
                    <div className="w-8 h-8 bg-gray-50 rounded-lg flex items-center justify-center mr-2">
                      <span>📧</span>
                    </div>
                    {lead.anymailfinder_email || lead.email || 'Email missing'}
                  </div>
                  {lead.linkedin_url && (
                    <div className="flex items-center text-sm text-gray-600">
                      <div className="w-8 h-8 bg-gray-50 rounded-lg flex items-center justify-center mr-2">
                        <span>💼</span>
                      </div>
                      LinkedIn Profile
                    </div>
                  )}
                  <div className="flex items-center text-sm text-gray-600">
                    <div className="w-8 h-8 bg-gray-50 rounded-lg flex items-center justify-center mr-2">
                      <span>📍</span>
                    </div>
                    {lead.address || 'Location unknown'}
                  </div>
                </div>

                <div className="flex justify-between items-center pt-4 border-t-2 border-gray-100">
                  <span
                    className={`px-3 py-1.5 rounded-full text-xs font-bold ${getStatusColor(
                      lead.status || 'new'
                    )}`}
                  >
                    {getStatusLabel(lead.status || 'new')}
                  </span>
                  <span className="text-brand-blue text-sm font-semibold group-hover:translate-x-1 transition-transform inline-block">
                    View Details →
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
