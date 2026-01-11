'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import Link from 'next/link';
import {
  Calendar,
  MapPin,
  Target,
  MoreVertical,
  Eye,
  Download,
  Trash2,
} from 'lucide-react';
import type { Hunt } from '@/lib/types';
import { formatDate } from '@/lib/utils';

interface HuntTableProps {
  hunts: Hunt[];
  onDelete?: (huntId: string) => void;
}

export function HuntTable({ hunts, onDelete }: HuntTableProps) {
  return (
    <div className="overflow-hidden bg-white rounded-[24px] border border-neutral-100 shadow-soft">
      {/* Table Header */}
      <div className="hidden md:grid grid-cols-[1.5fr_1fr_100px_140px_60px] gap-6 px-10 py-6 border-b border-neutral-50 bg-white">
        <div className="text-[10px] font-bold text-neutral-400 uppercase tracking-[0.1em]">
          Campaign
        </div>
        <div className="text-[10px] font-bold text-neutral-400 uppercase tracking-[0.1em]">
          Location
        </div>
        <div className="text-[10px] font-bold text-neutral-400 uppercase tracking-[0.1em]">
          Leads
        </div>
        <div className="text-[10px] font-bold text-neutral-400 uppercase tracking-[0.1em]">
          Status
        </div>
        <div></div>
      </div>

      {/* Table Body */}
      <div className="divide-y divide-neutral-50">
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
    pending: { label: 'Pending', color: 'text-neutral-500', bg: 'bg-neutral-100' },
    running: { label: 'Running', color: 'text-indigo-600', bg: 'bg-indigo-50 animate-pulse' },
    completed: { label: 'Completed', color: 'text-emerald-600', bg: 'bg-emerald-50' },
    failed: { label: 'Failed', color: 'text-rose-600', bg: 'bg-rose-50' },
  };

  const status = statusConfig[hunt.status] || statusConfig.pending;

  const rowHref = hunt.status === 'running'
    ? `/hunt/${hunt.hunt_id}/progress`
    : hunt.status === 'completed'
      ? `/hunt/${hunt.hunt_id}/results`
      : '#';

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: index * 0.05 }}
      className="group relative"
    >
      <Link
        href={rowHref}
        className="block md:grid grid-cols-[1.5fr_1fr_100px_140px_60px] gap-6 px-10 py-8 hover:bg-neutral-50 transition-all items-center"
      >
        {/* Date & Industry */}
        <div>
          <p className="font-bold text-neutral-900 text-base tracking-tight mb-1">
            {hunt.industry}
          </p>
          <div className="flex items-center gap-2 text-[11px] text-neutral-400 font-medium">
            <Calendar className="w-3.5 h-3.5" />
            {formatDate(hunt.created_at)}
          </div>
        </div>

        {/* Location */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-neutral-50 flex items-center justify-center text-neutral-400">
            <MapPin className="w-4 h-4" />
          </div>
          <span className="text-xs font-semibold text-neutral-600 truncate">{hunt.location}</span>
        </div>

        {/* Leads */}
        <div>
          <span className="text-sm font-bold text-neutral-900">
            {hunt.total_leads ?? hunt.target}
          </span>
        </div>

        {/* Status */}
        <div className="flex items-center">
          <span className={`px-4 py-1.5 rounded-full text-[11px] font-bold tracking-tight ${status.color} ${status.bg}`}>
            {status.label}
          </span>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end" onClick={(e) => e.preventDefault()}>
          <div className="relative">
            <button
              onClick={(e) => {
                e.preventDefault();
                setMenuOpen(!menuOpen);
              }}
              className="w-10 h-10 flex items-center justify-center border-2 border-transparent hover:border-black dark:hover:border-black text-neutral-400 hover:text-black dark:hover:text-black transition-all"
            >
              <MoreVertical className="w-5 h-5" />
            </button>

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
                    initial={{ opacity: 0, scale: 0.95, y: 10 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 10 }}
                    className="absolute right-0 top-full mt-2 w-52 bg-white dark:bg-white border-2 border-black dark:border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,0.1)] z-20 overflow-hidden font-mono"
                  >
                    <Link
                      href={rowHref}
                      className="flex items-center gap-3 px-5 py-4 text-[10px] font-black uppercase tracking-widest text-black dark:text-black hover:bg-black hover:text-white dark:hover:bg-black dark:hover:text-white transition-all"
                    >
                      <Eye className="w-4 h-4" />
                      <span>View_Data</span>
                    </Link>
                    {hunt.status === 'completed' && (
                      <Link
                        href={`/api/hunt/${hunt.hunt_id}/export?format=json`}
                        className="flex items-center gap-3 px-5 py-4 text-[10px] font-black uppercase tracking-widest text-black dark:text-black hover:bg-black hover:text-white dark:hover:bg-black dark:hover:text-white transition-all border-t-2 border-black dark:border-black"
                      >
                        <Download className="w-4 h-4" />
                        <span>Export_JSON</span>
                      </Link>
                    )}
                    {onDelete && (
                      <button
                        onClick={() => {
                          onDelete(hunt.hunt_id);
                          setMenuOpen(false);
                        }}
                        className="w-full flex items-center gap-3 px-5 py-4 text-[10px] font-black uppercase tracking-widest text-red-500 hover:bg-red-500 hover:text-white transition-all border-t-2 border-black dark:border-black"
                      >
                        <Trash2 className="w-4 h-4" />
                        <span>Delete_Data</span>
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
    <div className="px-6 py-24 flex flex-col items-center justify-center text-center">
      <div className="w-20 h-20 bg-neutral-50 dark:bg-neutral-950 border-2 border-dashed border-neutral-200 dark:border-neutral-800 flex items-center justify-center mb-6">
        <Target className="w-10 h-10 text-neutral-300 dark:text-neutral-700" />
      </div>
      <h3 className="text-xl font-black text-black dark:text-white uppercase tracking-tighter mb-2">
        Zero_Active_Hunts
      </h3>
      <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest font-mono">
        Initiate_New_Protocol_To_Begin_Extraction
      </p>
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
