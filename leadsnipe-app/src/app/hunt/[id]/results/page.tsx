'use client';

import { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { motion } from 'motion/react';
import {
  ArrowLeft,
  Target,
  MapPin,
  Users,
  Mail,
  Linkedin,
  DollarSign,
  Download,
  Search,
  Filter,
  Check,
  X,
  FileJson,
  FileSpreadsheet,
  MoreVertical,
} from 'lucide-react';
import { StatsCard, LeadCard, LeadCardSkeleton } from '@/components';
import type { HuntDetails, Lead } from '@/lib/types';
import { formatDate, formatCurrency, downloadJson, downloadCsv } from '@/lib/utils';

interface PageProps {
  params: Promise<{ id: string }>;
}

import { api } from '@/lib/api';

// ... (other imports)

export default function HuntResultsPage({ params }: PageProps) {
  const { id: huntId } = use(params);

  const [huntDetails, setHuntDetails] = useState<HuntDetails | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [filteredLeads, setFilteredLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLeads, setSelectedLeads] = useState<Set<string>>(new Set());

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCeoEmail, setFilterCeoEmail] = useState(false);
  const [filterLinkedIn, setFilterLinkedIn] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);

  // Fetch hunt results
  useEffect(() => {
    async function fetchResults() {
      try {
        const data = await api.getHuntDetails(huntId);
        setHuntDetails(data);
        setLeads(data.leads || []);
        setFilteredLeads(data.leads || []);
      } catch (err) {
        console.error('Failed to fetch results:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchResults();
  }, [huntId]);

  // Apply filters
  useEffect(() => {
    let result = [...leads];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(lead =>
        lead.name.toLowerCase().includes(query) ||
        lead.address.toLowerCase().includes(query) ||
        lead.decision_maker?.full_name?.toLowerCase().includes(query)
      );
    }

    // CEO email filter
    if (filterCeoEmail) {
      result = result.filter(lead =>
        lead.decision_maker?.status === 'valid' && lead.decision_maker?.email
      );
    }

    // LinkedIn filter
    if (filterLinkedIn) {
      result = result.filter(lead => lead.decision_maker?.linkedin_url);
    }

    setFilteredLeads(result);
  }, [leads, searchQuery, filterCeoEmail, filterLinkedIn]);

  // Selection handlers
  const handleSelectLead = (id: string) => {
    const newSelected = new Set(selectedLeads);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedLeads(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedLeads.size === filteredLeads.length) {
      setSelectedLeads(new Set());
    } else {
      setSelectedLeads(new Set(filteredLeads.map(l => l.id)));
    }
  };

  // Export handlers
  const handleExportJson = () => {
    const dataToExport = selectedLeads.size > 0
      ? filteredLeads.filter(l => selectedLeads.has(l.id))
      : filteredLeads;
    downloadJson(dataToExport, `leadsnipe_${huntId}.json`);
    setShowExportMenu(false);
  };

  const handleExportCsv = () => {
    const dataToExport = selectedLeads.size > 0
      ? filteredLeads.filter(l => selectedLeads.has(l.id))
      : filteredLeads;

    // Flatten the data for CSV
    const flatData = dataToExport.map(lead => ({
      name: lead.name,
      address: lead.address,
      phone: lead.phone,
      website: lead.website,
      business_email: lead.email,
      rating: lead.rating,
      reviews: lead.user_ratings_total,
      decision_maker_name: lead.decision_maker?.full_name || '',
      decision_maker_title: lead.decision_maker?.job_title || '',
      decision_maker_email: lead.decision_maker?.email || '',
      linkedin_url: lead.decision_maker?.linkedin_url || '',
    }));

    downloadCsv(flatData, `leadsnipe_${huntId}.csv`);
    setShowExportMenu(false);
  };

  // Stats
  const stats = {
    total: leads.length,
    withCeoEmail: leads.filter(l => l.decision_maker?.status === 'valid').length,
    withLinkedIn: leads.filter(l => l.decision_maker?.linkedin_url).length,
    cost: huntDetails?.stats?.cost || 0,
  };

  return (
    <div className="min-h-screen py-12 px-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8"
        >
          <div>
            <Link
              href="/"
              className="inline-flex items-center gap-2 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors mb-4"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Dashboard</span>
            </Link>

            <h1 className="font-[family-name:var(--font-display)] text-2xl md:text-3xl font-bold text-[var(--color-text-primary)]">
              {huntDetails?.industry || 'Loading...'} in {huntDetails?.location}
            </h1>

            <div className="flex items-center gap-4 text-sm text-[var(--color-text-muted)] mt-2">
              <span>{stats.total} leads found</span>
              <span>|</span>
              <span>{formatDate(huntDetails?.created_at || new Date().toISOString())}</span>
            </div>
          </div>

          {/* Export Actions */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setShowExportMenu(!showExportMenu)}
                className="flex items-center gap-2 px-5 py-2.5 bg-black dark:bg-white rounded-xl font-bold text-white dark:text-black shadow-lg"
              >
                <Download className="w-4 h-4" />
                <span>Export</span>
                {selectedLeads.size > 0 && (
                  <span className="px-2 py-0.5 bg-white/20 dark:bg-black/20 rounded-md text-xs">
                    {selectedLeads.size}
                  </span>
                )}
              </motion.button>

              {showExportMenu && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setShowExportMenu(false)}
                  />
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: -10 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    className="absolute right-0 top-full mt-2 w-48 bg-white dark:bg-black border border-neutral-200 dark:border-neutral-800 rounded-xl shadow-xl z-20 overflow-hidden"
                  >
                    <button
                      onClick={handleExportJson}
                      className="w-full flex items-center gap-3 px-4 py-3 text-sm font-bold text-neutral-600 hover:bg-neutral-50 dark:hover:bg-neutral-900 transition-colors"
                    >
                      <FileJson className="w-4 h-4" />
                      <span>Download JSON</span>
                    </button>
                    <button
                      onClick={handleExportCsv}
                      className="w-full flex items-center gap-3 px-4 py-3 text-sm font-bold text-neutral-600 hover:bg-neutral-50 dark:hover:bg-neutral-900 transition-colors"
                    >
                      <FileSpreadsheet className="w-4 h-4" />
                      <span>Download CSV</span>
                    </button>
                  </motion.div>
                </>
              )}
            </div>

            <button className="p-2.5 bg-white dark:bg-black border border-neutral-200 dark:border-neutral-800 rounded-xl text-neutral-400 hover:text-black dark:hover:text-white transition-colors">
              <MoreVertical className="w-5 h-5" />
            </button>
          </div>
        </motion.div>

        {/* Stats Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
        >
          <StatsCard
            title="Total Leads"
            value={stats.total}
            icon={Users}
            variant="white"
          />
          <StatsCard
            title="CEO Emails"
            value={stats.withCeoEmail}
            icon={Mail}
            variant="white"
            trend={`${Math.round((stats.withCeoEmail / stats.total) * 100) || 0}% success`}
            trendUp={true}
          />
          <StatsCard
            title="LinkedIn Found"
            value={stats.withLinkedIn}
            icon={Linkedin}
            variant="white"
          />
          <StatsCard
            title="Total Cost"
            value={formatCurrency(stats.cost)}
            icon={DollarSign}
            variant="white"
          />
        </motion.div>

        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex flex-col md:flex-row gap-4 mb-6"
        >
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
            <input
              type="text"
              placeholder="Search by name, location, or contact..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-field pl-11"
            />
          </div>

          {/* Filter Toggles */}
          <div className="flex items-center gap-3">
            <FilterToggle
              active={filterCeoEmail}
              onClick={() => setFilterCeoEmail(!filterCeoEmail)}
              icon={Mail}
              label="Has CEO Email"
            />
            <FilterToggle
              active={filterLinkedIn}
              onClick={() => setFilterLinkedIn(!filterLinkedIn)}
              icon={Linkedin}
              label="Has LinkedIn"
            />
          </div>
        </motion.div>

        {/* Bulk Actions & Selection */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="flex items-center justify-between mb-8 bg-black p-4 px-6 rounded-[24px] text-white shadow-2xl"
        >
          <button
            onClick={handleSelectAll}
            className="flex items-center gap-3 text-sm font-black uppercase tracking-widest transition-all"
          >
            <div className={`
              w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all
              ${selectedLeads.size === filteredLeads.length && filteredLeads.length > 0
                ? 'bg-white border-white'
                : 'border-white/20 hover:border-white'
              }
            `}>
              {selectedLeads.size === filteredLeads.length && filteredLeads.length > 0 && (
                <Check className="w-4 h-4 text-black" strokeWidth={4} />
              )}
            </div>
            <span>
              {selectedLeads.size === filteredLeads.length && filteredLeads.length > 0
                ? 'Deselect All Leads'
                : 'Select All Leads'
              }
            </span>
          </button>

          <div className="text-xs font-black uppercase tracking-widest text-white/40">
            Showing {filteredLeads.length} of {leads.length}
            {selectedLeads.size > 0 && (
              <span className="ml-3 text-white">
                ({selectedLeads.size} selected)
              </span>
            )}
          </div>
        </motion.div>

        {/* Lead Cards Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {loading ? (
            <>
              <LeadCardSkeleton />
              <LeadCardSkeleton />
              <LeadCardSkeleton />
              <LeadCardSkeleton />
              <LeadCardSkeleton />
              <LeadCardSkeleton />
            </>
          ) : filteredLeads.length === 0 ? (
            <div className="col-span-full py-16 text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-[var(--color-elevated)] rounded-2xl flex items-center justify-center">
                <Search className="w-8 h-8 text-[var(--color-text-muted)]" />
              </div>
              <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
                No leads found
              </h3>
              <p className="text-sm text-[var(--color-text-muted)]">
                Try adjusting your filters or search query
              </p>
            </div>
          ) : (
            filteredLeads.map((lead, index) => (
              <LeadCard
                key={lead.id}
                lead={lead}
                isSelected={selectedLeads.has(lead.id)}
                onSelect={handleSelectLead}
                delay={index * 0.05}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}

interface FilterToggleProps {
  active: boolean;
  onClick: () => void;
  icon: React.ElementType;
  label: string;
}

function FilterToggle({ active, onClick, icon: Icon, label }: FilterToggleProps) {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`
        flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all
        ${active
          ? 'bg-black text-white dark:bg-white dark:text-black border-black dark:border-white'
          : 'bg-white dark:bg-black text-neutral-500 border-neutral-200 dark:border-neutral-800 hover:border-black dark:hover:border-white'
        }
      `}
    >
      <Icon className="w-4 h-4" />
      <span className="hidden sm:inline">{label}</span>
      {active && <X className="w-3 h-3" />}
    </motion.button>
  );
}
