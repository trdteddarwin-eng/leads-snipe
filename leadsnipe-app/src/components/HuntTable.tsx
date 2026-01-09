'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import Link from 'next/link';
import {
  Calendar,
  MapPin,
  Target,
  Users,
  MoreVertical,
  Eye,
  Download,
  Trash2,
  Play,
  CheckCircle2,
  Clock,
  AlertCircle,
} from 'lucide-react';
import type { Hunt } from '@/lib/types';
import { formatDate, formatCurrency } from '@/lib/utils';

interface HuntTableProps {
  hunts: Hunt[];
  onDelete?: (huntId: string) => void;
}

export function HuntTable({ hunts, onDelete }: HuntTableProps) {
  return (
    <div className="overflow-hidden">
      {/* Table Header */}
      <div className="hidden md:grid grid-cols-[1fr_1fr_100px_100px_80px] gap-4 px-6 py-3 border-b border-[var(--color-border)] text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4" />
          <span>Date & Industry</span>
        </div>
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4" />
          <span>Location</span>
        </div>
        <div className="flex items-center gap-2">
          <Users className="w-4 h-4" />
          <span>Leads</span>
        </div>
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4" />
          <span>Status</span>
        </div>
        <div></div>
      </div>

      {/* Table Body */}
      <div className="divide-y divide-[var(--color-border)]">
        {hunts.length === 0 ? (
          <EmptyState />
        ) : (
          hunts.map((hunt, index) => (
            <HuntRow key={hunt.hunt_id} hunt={hunt} index={index} onDelete={onDelete} />
          ))
        )}
      </div>
    </div>
  );
}

interface HuntRowProps {
  hunt: Hunt;
  index: number;
  onDelete?: (huntId: string) => void;
}

function HuntRow({ hunt, index, onDelete }: HuntRowProps) {
  const [menuOpen, setMenuOpen] = useState(false);

  const statusConfig = {
    pending: {
      icon: Clock,
      label: 'Pending',
      color: 'text-[var(--color-warning)]',
      bg: 'bg-[var(--color-warning)]/10',
    },
    running: {
      icon: Play,
      label: 'Running',
      color: 'text-[var(--color-brand-purple)]',
      bg: 'bg-[var(--color-brand-purple)]/10',
    },
    completed: {
      icon: CheckCircle2,
      label: 'Complete',
      color: 'text-[var(--color-success)]',
      bg: 'bg-[var(--color-success)]/10',
    },
    failed: {
      icon: AlertCircle,
      label: 'Failed',
      color: 'text-[var(--color-error)]',
      bg: 'bg-[var(--color-error)]/10',
    },
  };

  const status = statusConfig[hunt.status];
  const StatusIcon = status.icon;

  const rowHref = hunt.status === 'running'
    ? `/hunt/${hunt.hunt_id}/progress`
    : hunt.status === 'completed'
      ? `/hunt/${hunt.hunt_id}/results`
      : '#';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="table-row"
    >
      <Link
        href={rowHref}
        className="block md:grid grid-cols-[1fr_1fr_100px_100px_80px] gap-4 px-6 py-4 hover:bg-[var(--color-bg-gray-50)] transition-colors border-b border-[var(--color-border)] last:border-0"
      >
        {/* Date & Industry */}
        <div className="mb-2 md:mb-0">
          <p className="text-sm text-[var(--color-text-muted)] mb-1 md:hidden">
            {formatDate(hunt.created_at)}
          </p>
          <p className="font-medium text-[var(--color-text-primary)]">
            {hunt.industry}
          </p>
          <p className="text-sm text-[var(--color-text-muted)] hidden md:block">
            {formatDate(hunt.created_at)}
          </p>
        </div>

        {/* Location */}
        <div className="flex items-center gap-2 mb-2 md:mb-0">
          <MapPin className="w-4 h-4 text-[var(--color-text-muted)] md:hidden" />
          <span className="text-[var(--color-text-secondary)]">{hunt.location}</span>
        </div>

        {/* Leads */}
        <div className="flex items-center gap-2 mb-2 md:mb-0">
          <Users className="w-4 h-4 text-[var(--color-text-muted)] md:hidden" />
          <div>
            <span className="font-semibold text-[var(--color-text-primary)]">
              {hunt.total_leads ?? hunt.target}
            </span>
            {hunt.cost !== undefined && (
              <p className="text-xs text-[var(--color-text-muted)]">
                {formatCurrency(hunt.cost)}
              </p>
            )}
          </div>
        </div>

        {/* Status */}
        <div className="flex items-center">
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${status.color} ${status.bg}`}>
            <StatusIcon className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{status.label}</span>
          </span>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end" onClick={(e) => e.preventDefault()}>
          <div className="relative">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={(e) => {
                e.preventDefault();
                setMenuOpen(!menuOpen);
              }}
              className="p-2 rounded-lg hover:bg-[var(--color-bg-gray-50)] text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
            >
              <MoreVertical className="w-4 h-4" />
            </motion.button>

            <AnimatePresence>
              {menuOpen && (
                <>
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-10"
                    onClick={() => setMenuOpen(false)}
                  />
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: -10 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: -10 }}
                    className="absolute right-0 top-full mt-1 w-48 bg-white border border-[var(--color-border)] rounded-xl shadow-xl z-20 overflow-hidden"
                  >
                    <Link
                      href={rowHref}
                      className="flex items-center gap-3 px-4 py-3 text-sm text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-gray-50)] hover:text-[var(--color-text-primary)] transition-colors"
                    >
                      <Eye className="w-4 h-4" />
                      <span>View Details</span>
                    </Link>
                    {hunt.status === 'completed' && (
                      <Link
                        href={`/api/hunt/${hunt.hunt_id}/export?format=json`}
                        className="flex items-center gap-3 px-4 py-3 text-sm text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-gray-50)] hover:text-[var(--color-text-primary)] transition-colors"
                      >
                        <Download className="w-4 h-4" />
                        <span>Download JSON</span>
                      </Link>
                    )}
                    {onDelete && (
                      <button
                        onClick={() => {
                          onDelete(hunt.hunt_id);
                          setMenuOpen(false);
                        }}
                        className="w-full flex items-center gap-3 px-4 py-3 text-sm text-[var(--color-error)] hover:bg-[var(--color-error)]/10 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                        <span>Delete Hunt</span>
                      </button>
                    )}
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}

function EmptyState() {
  return (
    <div className="px-6 py-16 text-center">
      <div className="w-16 h-16 mx-auto mb-4 bg-[var(--color-bg-gray-50)] rounded-2xl flex items-center justify-center">
        <Target className="w-8 h-8 text-[var(--color-text-muted)]" />
      </div>
      <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
        No hunts yet
      </h3>
      <p className="text-sm text-[var(--color-text-muted)] mb-6 max-w-sm mx-auto">
        Start your first lead hunt to find decision makers at businesses in your target market.
      </p>
      <Link
        href="/hunt/new"
        className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-[var(--color-brand-blue)] to-purple-600 rounded-xl font-semibold text-white hover:opacity-90 transition-opacity"
      >
        <Target className="w-4 h-4" />
        <span>Start First Hunt</span>
      </Link>
    </div>
  );
}

// Skeleton version
export function HuntTableSkeleton() {
  return (
    <div className="overflow-hidden">
      <div className="hidden md:grid grid-cols-[1fr_1fr_100px_100px_80px] gap-4 px-6 py-3 border-b border-[var(--color-border)]">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-4 skeleton w-20" />
        ))}
      </div>
      <div>
        {[...Array(5)].map((_, i) => (
          <div key={i} className="px-6 py-4 md:grid grid-cols-[1fr_1fr_100px_100px_80px] gap-4 border-b border-[var(--color-border)]">
            <div className="space-y-2 mb-2 md:mb-0">
              <div className="h-4 skeleton w-32" />
              <div className="h-3 skeleton w-24" />
            </div>
            <div className="h-4 skeleton w-28 mb-2 md:mb-0" />
            <div className="h-4 skeleton w-12 mb-2 md:mb-0" />
            <div className="h-6 skeleton w-20 rounded-full" />
          </div>
        ))}
      </div>
    </div>
  );
}
