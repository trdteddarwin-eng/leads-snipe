'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion, AnimatePresence } from 'motion/react';
import {
  ArrowLeft,
  Target,
  MapPin,
  Users,
  Briefcase,
  DollarSign,
  Clock,
  Loader2,
  Sparkles,
  Info,
} from 'lucide-react';
import {
  INDUSTRY_SUGGESTIONS,
  LOCATION_SUGGESTIONS,
  DECISION_MAKER_CATEGORIES,
} from '@/lib/types';
import { calculateEstimatedCost, calculateEstimatedTime, formatCurrency, formatDuration } from '@/lib/utils';
import { api } from '@/lib/api';

export default function NewHunt() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    industry: '',
    location: '',
    target: 25,
    category: 'ceo',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showIndustrySuggestions, setShowIndustrySuggestions] = useState(false);
  const [showLocationSuggestions, setShowLocationSuggestions] = useState(false);
  const industryRef = useRef<HTMLDivElement>(null);
  const locationRef = useRef<HTMLDivElement>(null);

  // Calculate estimates
  const estimatedCost = calculateEstimatedCost(formData.target);
  const estimatedTime = calculateEstimatedTime(formData.target);

  // Filter suggestions based on input
  const filteredIndustries = INDUSTRY_SUGGESTIONS.filter(i =>
    i.toLowerCase().includes(formData.industry.toLowerCase())
  );
  const filteredLocations = LOCATION_SUGGESTIONS.filter(l =>
    l.toLowerCase().includes(formData.location.toLowerCase())
  );

  // Close dropdowns on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (industryRef.current && !industryRef.current.contains(event.target as Node)) {
        setShowIndustrySuggestions(false);
      }
      if (locationRef.current && !locationRef.current.contains(event.target as Node)) {
        setShowLocationSuggestions(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.industry || !formData.location) return;

    setIsSubmitting(true);

    try {
      const huntId = await api.createHunt(formData);
      router.push(`/hunt/${huntId}/progress`);
    } catch (error) {
      console.error('Failed to create hunt:', error);
      setIsSubmitting(false);
    }
  };

  const isValid = formData.industry.trim() && formData.location.trim();

  return (
    <div className="py-12 px-6 animate-in fade-in duration-700">
      <div className="max-w-3xl mx-auto">
        {/* Back button */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="mb-10"
        >
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-neutral-500 hover:text-neutral-900 font-bold text-xs transition-colors group"
          >
            <div className="w-8 h-8 rounded-full bg-white border border-neutral-100 flex items-center justify-center group-hover:bg-neutral-50 transition-colors shadow-sm">
              <ArrowLeft className="w-4 h-4" />
            </div>
            <span>Back to Dashboard</span>
          </Link>
        </motion.div>

        {/* Form Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-[32px] border border-neutral-100 p-8 md:p-14 shadow-premium"
        >
          {/* Header */}
          <div className="flex items-center gap-6 mb-12">
            <div className="w-16 h-16 bg-neutral-900 rounded-[22px] flex items-center justify-center shadow-2xl shadow-neutral-900/40">
              <Target className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-black text-neutral-900 tracking-tight">
                Create New Lead Hunt
              </h1>
              <p className="text-sm text-neutral-600 font-medium mt-1">
                Find decision makers in your target market
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-10">
            {/* Industry Input */}
            <div ref={industryRef} className="relative">
              <label className="block text-[11px] font-extrabold text-neutral-900 uppercase tracking-widest mb-3">
                Industry
              </label>
              <div className="relative group">
                <Briefcase className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400 group-focus-within:text-neutral-900 transition-colors" />
                <input
                  type="text"
                  value={formData.industry}
                  onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                  onFocus={() => setShowIndustrySuggestions(true)}
                  placeholder="e.g., HVAC contractor, Dentist, Plumber"
                  className="w-full h-14 bg-white border border-neutral-200 rounded-2xl pl-13 pr-4 text-sm font-semibold outline-none focus:border-neutral-900 focus:ring-4 focus:ring-neutral-900/5 transition-all text-neutral-900 placeholder:text-neutral-300"
                  required
                />
              </div>

              <AnimatePresence>
                {showIndustrySuggestions && filteredIndustries.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute z-10 top-full left-0 right-0 mt-3 bg-white border border-neutral-100 rounded-2xl shadow-premium overflow-hidden max-h-60 overflow-y-auto"
                  >
                    {filteredIndustries.map((industry) => (
                      <button
                        key={industry}
                        type="button"
                        onClick={() => {
                          setFormData({ ...formData, industry });
                          setShowIndustrySuggestions(false);
                        }}
                        className="w-full px-5 py-3.5 text-left text-sm font-bold text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900 transition-colors"
                      >
                        {industry}
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Location Input */}
            <div ref={locationRef} className="relative">
              <label className="block text-[11px] font-extrabold text-neutral-900 uppercase tracking-widest mb-3">
                Location
              </label>
              <div className="relative group">
                <MapPin className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400 group-focus-within:text-neutral-900 transition-colors" />
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  onFocus={() => setShowLocationSuggestions(true)}
                  placeholder="e.g., New Jersey, Phoenix area"
                  className="w-full h-14 bg-white border border-neutral-200 rounded-2xl pl-13 pr-4 text-sm font-semibold outline-none focus:border-neutral-900 focus:ring-4 focus:ring-neutral-900/5 transition-all text-neutral-900 placeholder:text-neutral-300"
                  required
                />
              </div>

              <AnimatePresence>
                {showLocationSuggestions && filteredLocations.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute z-10 top-full left-0 right-0 mt-3 bg-white border border-neutral-100 rounded-2xl shadow-premium overflow-hidden max-h-60 overflow-y-auto"
                  >
                    {filteredLocations.map((location) => (
                      <button
                        key={location}
                        type="button"
                        onClick={() => {
                          setFormData({ ...formData, location });
                          setShowLocationSuggestions(false);
                        }}
                        className="w-full px-5 py-3.5 text-left text-sm font-bold text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900 transition-colors"
                      >
                        {location}
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Lead Count Slider */}
            <div className="space-y-5">
              <label className="block text-[11px] font-extrabold text-neutral-900 uppercase tracking-widest">
                Target Quantity
              </label>

              <div className="bg-neutral-50/50 p-8 rounded-2xl border border-neutral-100 space-y-8">
                <div className="flex items-center justify-between px-2">
                  <span className="text-xs font-black text-neutral-400 uppercase tracking-tighter">Min_10</span>
                  <div className="flex flex-col items-center">
                    <span className="text-5xl font-black text-neutral-900 tabular-nums">
                      {formData.target}
                    </span>
                    <span className="text-[10px] font-black text-neutral-400 uppercase tracking-[0.2em] mt-2">LEADS_TOTAL</span>
                  </div>
                  <span className="text-xs font-black text-neutral-400 uppercase tracking-tighter">Max_100</span>
                </div>

                <input
                  type="range"
                  min="10"
                  max="100"
                  step="5"
                  value={formData.target}
                  onChange={(e) => setFormData({ ...formData, target: parseInt(e.target.value) })}
                  className="w-full h-2 bg-neutral-200 rounded-lg appearance-none cursor-pointer accent-neutral-900"
                />
              </div>
            </div>

            {/* Decision Maker Category */}
            <div>
              <label className="block text-[11px] font-extrabold text-neutral-900 uppercase tracking-widest mb-3">
                Decision Maker Role
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full bg-neutral-50/50 border border-neutral-100 rounded-xl py-4 px-4 text-sm font-semibold outline-none focus:bg-white focus:ring-2 focus:ring-black/5 transition-all text-neutral-900 cursor-pointer appearance-none"
              >
                {DECISION_MAKER_CATEGORIES.map((cat) => (
                  <option key={cat.value} value={cat.value}>
                    {cat.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Estimation Panel */}
            <div className="bg-black rounded-[32px] p-10 text-white space-y-10 shadow-2xl">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center border border-white/10">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <span className="text-[11px] font-black uppercase tracking-[0.2em] text-white/50">
                  Estimated Deployment Yield
                </span>
              </div>

              <div className="grid grid-cols-2 gap-12">
                <div className="space-y-2">
                  <p className="text-4xl font-black tracking-tighter tabular-nums">{formatCurrency(estimatedCost)}</p>
                  <p className="text-[10px] font-black text-white/40 uppercase tracking-widest">Total Estimated Cost</p>
                </div>

                <div className="space-y-2">
                  <p className="text-4xl font-black tracking-tighter tabular-nums">~{formatDuration(estimatedTime)}</p>
                  <p className="text-[10px] font-black text-white/40 uppercase tracking-widest">Calculated Time</p>
                </div>
              </div>

              <div className="flex items-start gap-4 pt-8 border-t border-white/10">
                <Info className="w-5 h-5 text-white/30 flex-shrink-0 mt-0.5" />
                <p className="text-[11px] text-white/40 font-bold leading-relaxed uppercase tracking-wider">
                  Cost is $0.04 per valid decision maker email. LinkedIn discovery is included.
                  Final yield may vary based on data density in target location.
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4 pt-4">
              <Link href="/" className="flex-1">
                <button
                  type="button"
                  className="w-full py-4.5 px-6 rounded-2xl font-bold text-neutral-400 hover:text-neutral-900 hover:bg-neutral-50 transition-all text-sm"
                >
                  Cancel
                </button>
              </Link>

              <button
                type="submit"
                disabled={!isValid || isSubmitting}
                className={`
                  flex-1 flex items-center justify-center gap-3 py-4.5 px-6 rounded-2xl font-bold text-sm transition-all shadow-xl
                  ${isValid && !isSubmitting
                    ? 'bg-neutral-900 text-white shadow-neutral-900/20 hover:bg-neutral-800'
                    : 'bg-neutral-100 text-neutral-300 cursor-not-allowed shadow-none'
                  }
                `}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Deploying Snipers...</span>
                  </>
                ) : (
                  <>
                    <Target className="w-5 h-5" />
                    <span>Generate Leads</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </div>
  );
}
