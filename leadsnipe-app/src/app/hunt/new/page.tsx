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
      const response = await fetch('/api/hunt/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        const data = await response.json();
        router.push(`/hunt/${data.hunt_id}/progress`);
      } else {
        throw new Error('Failed to create hunt');
      }
    } catch (error) {
      console.error('Failed to create hunt:', error);
      setIsSubmitting(false);
    }
  };

  const isValid = formData.industry.trim() && formData.location.trim();

  return (
    <div className="min-h-screen py-12 px-6">
      <div className="max-w-2xl mx-auto">
        {/* Back button */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="mb-8"
        >
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Dashboard</span>
          </Link>
        </motion.div>

        {/* Form Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="relative"
        >
          {/* Gradient border effect */}
          <div className="absolute -inset-px rounded-3xl bg-gradient-to-r from-[var(--color-brand-purple)] via-[var(--color-brand-blue)] to-[var(--color-brand-cyan)] opacity-20" />

          <div className="relative bg-[var(--color-surface)] border border-[var(--color-border)] rounded-3xl p-8 md:p-10">
            {/* Header */}
            <div className="flex items-center gap-4 mb-8">
              <div className="w-14 h-14 bg-gradient-to-br from-[var(--color-brand-purple)] to-[var(--color-brand-blue)] rounded-2xl flex items-center justify-center shadow-lg shadow-[var(--color-brand-purple)]/20">
                <Target className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="font-[family-name:var(--font-display)] text-2xl font-bold text-[var(--color-text-primary)]">
                  Create New Lead Hunt
                </h1>
                <p className="text-sm text-[var(--color-text-muted)]">
                  Find decision makers in your target market
                </p>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Industry Input */}
              <div ref={industryRef} className="relative">
                <label className="flex items-center gap-2 text-sm font-medium text-[var(--color-text-secondary)] mb-2">
                  <Briefcase className="w-4 h-4" />
                  Industry *
                </label>
                <input
                  type="text"
                  value={formData.industry}
                  onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                  onFocus={() => setShowIndustrySuggestions(true)}
                  placeholder="e.g., HVAC contractor, Dentist, Plumber"
                  className="input-field"
                  required
                />

                <AnimatePresence>
                  {showIndustrySuggestions && filteredIndustries.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="absolute z-10 top-full left-0 right-0 mt-2 bg-[var(--color-elevated)] border border-[var(--color-border)] rounded-xl shadow-xl overflow-hidden max-h-48 overflow-y-auto"
                    >
                      {filteredIndustries.map((industry) => (
                        <button
                          key={industry}
                          type="button"
                          onClick={() => {
                            setFormData({ ...formData, industry });
                            setShowIndustrySuggestions(false);
                          }}
                          className="w-full px-4 py-3 text-left text-sm text-[var(--color-text-secondary)] hover:bg-[var(--color-surface)] hover:text-[var(--color-text-primary)] transition-colors"
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
                <label className="flex items-center gap-2 text-sm font-medium text-[var(--color-text-secondary)] mb-2">
                  <MapPin className="w-4 h-4" />
                  Location *
                </label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  onFocus={() => setShowLocationSuggestions(true)}
                  placeholder="e.g., New Jersey, Phoenix area"
                  className="input-field"
                  required
                />

                <AnimatePresence>
                  {showLocationSuggestions && filteredLocations.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="absolute z-10 top-full left-0 right-0 mt-2 bg-[var(--color-elevated)] border border-[var(--color-border)] rounded-xl shadow-xl overflow-hidden max-h-48 overflow-y-auto"
                    >
                      {filteredLocations.map((location) => (
                        <button
                          key={location}
                          type="button"
                          onClick={() => {
                            setFormData({ ...formData, location });
                            setShowLocationSuggestions(false);
                          }}
                          className="w-full px-4 py-3 text-left text-sm text-[var(--color-text-secondary)] hover:bg-[var(--color-surface)] hover:text-[var(--color-text-primary)] transition-colors"
                        >
                          {location}
                        </button>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Lead Count Slider */}
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-[var(--color-text-secondary)] mb-4">
                  <Users className="w-4 h-4" />
                  Number of Leads *
                </label>

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-[var(--color-text-muted)]">10</span>
                    <span className="px-4 py-2 bg-gradient-to-r from-[var(--color-brand-purple)] to-[var(--color-brand-blue)] rounded-lg text-white font-bold text-lg">
                      {formData.target}
                    </span>
                    <span className="text-sm text-[var(--color-text-muted)]">100</span>
                  </div>

                  <input
                    type="range"
                    min="10"
                    max="100"
                    step="5"
                    value={formData.target}
                    onChange={(e) => setFormData({ ...formData, target: parseInt(e.target.value) })}
                    className="w-full h-2 bg-[var(--color-abyss)] rounded-lg appearance-none cursor-pointer
                      [&::-webkit-slider-thumb]:appearance-none
                      [&::-webkit-slider-thumb]:w-5
                      [&::-webkit-slider-thumb]:h-5
                      [&::-webkit-slider-thumb]:bg-gradient-to-r
                      [&::-webkit-slider-thumb]:from-[var(--color-brand-purple)]
                      [&::-webkit-slider-thumb]:to-[var(--color-brand-blue)]
                      [&::-webkit-slider-thumb]:rounded-full
                      [&::-webkit-slider-thumb]:cursor-pointer
                      [&::-webkit-slider-thumb]:shadow-lg
                      [&::-webkit-slider-thumb]:shadow-[var(--color-brand-purple)]/30
                      [&::-webkit-slider-thumb]:transition-transform
                      [&::-webkit-slider-thumb]:hover:scale-110
                    "
                  />
                </div>
              </div>

              {/* Decision Maker Category */}
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-[var(--color-text-secondary)] mb-2">
                  <Target className="w-4 h-4" />
                  Decision Maker Category
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="input-field cursor-pointer"
                >
                  {DECISION_MAKER_CATEGORIES.map((cat) => (
                    <option key={cat.value} value={cat.value}>
                      {cat.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Estimation Panel */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-[var(--color-abyss)] border border-[var(--color-border)] rounded-2xl p-5"
              >
                <div className="flex items-center gap-2 mb-4">
                  <Sparkles className="w-4 h-4 text-[var(--color-brand-cyan)]" />
                  <span className="text-sm font-medium text-[var(--color-text-primary)]">
                    Estimated Results
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-[var(--color-brand-purple)]/10 rounded-xl flex items-center justify-center">
                      <DollarSign className="w-5 h-5 text-[var(--color-brand-purple)]" />
                    </div>
                    <div>
                      <p className="text-lg font-bold text-[var(--color-text-primary)]">
                        {formatCurrency(estimatedCost)}
                      </p>
                      <p className="text-xs text-[var(--color-text-muted)]">Estimated cost</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-[var(--color-brand-blue)]/10 rounded-xl flex items-center justify-center">
                      <Clock className="w-5 h-5 text-[var(--color-brand-blue)]" />
                    </div>
                    <div>
                      <p className="text-lg font-bold text-[var(--color-text-primary)]">
                        ~{formatDuration(estimatedTime)}
                      </p>
                      <p className="text-xs text-[var(--color-text-muted)]">Estimated time</p>
                    </div>
                  </div>
                </div>

                <div className="flex items-start gap-2 mt-4 pt-4 border-t border-[var(--color-border)]">
                  <Info className="w-4 h-4 text-[var(--color-text-muted)] flex-shrink-0 mt-0.5" />
                  <p className="text-xs text-[var(--color-text-muted)]">
                    Cost is $0.04 per valid CEO email found. LinkedIn discovery is free.
                    Actual results may vary based on industry and location.
                  </p>
                </div>
              </motion.div>

              {/* Action Buttons */}
              <div className="flex gap-4 pt-4">
                <Link href="/" className="flex-1">
                  <button
                    type="button"
                    className="w-full py-4 px-6 bg-[var(--color-elevated)] border border-[var(--color-border)] rounded-xl font-semibold text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:border-[var(--color-border-light)] transition-colors"
                  >
                    Cancel
                  </button>
                </Link>

                <motion.button
                  type="submit"
                  disabled={!isValid || isSubmitting}
                  whileHover={isValid && !isSubmitting ? { scale: 1.02 } : {}}
                  whileTap={isValid && !isSubmitting ? { scale: 0.98 } : {}}
                  className={`
                    flex-1 flex items-center justify-center gap-3 py-4 px-6 rounded-xl font-semibold text-white transition-all
                    ${isValid && !isSubmitting
                      ? 'bg-gradient-to-r from-[var(--color-brand-purple)] to-[var(--color-brand-blue)] shadow-lg shadow-[var(--color-brand-purple)]/25 hover:shadow-[var(--color-brand-purple)]/40'
                      : 'bg-[var(--color-elevated)] text-[var(--color-text-muted)] cursor-not-allowed'
                    }
                  `}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>Starting Hunt...</span>
                    </>
                  ) : (
                    <>
                      <Target className="w-5 h-5" />
                      <span>Generate Leads</span>
                    </>
                  )}
                </motion.button>
              </div>
            </form>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
