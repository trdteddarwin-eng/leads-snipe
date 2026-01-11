'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  Building2,
  MapPin,
  Star,
  User,
  Mail,
  Phone,
  Globe,
  Linkedin,
  Copy,
  Check,
  ExternalLink,
  ChevronDown,
} from 'lucide-react';
import type { Lead } from '@/lib/types';
import { extractDomain, copyToClipboard } from '@/lib/utils';

interface LeadCardProps {
  lead: Lead;
  isSelected?: boolean;
  onSelect?: (id: string) => void;
  delay?: number;
}

export function LeadCard({ lead, isSelected, onSelect, delay = 0 }: LeadCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const handleCopy = async (text: string, field: string) => {
    await copyToClipboard(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const hasCeoEmail = lead.decision_maker?.status === 'valid' && lead.decision_maker?.email;
  const hasLinkedIn = !!lead.decision_maker?.linkedin_url;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: 'easeOut' }}
      className={`
        group relative bg-white border border-neutral-100 rounded-[28px] overflow-hidden transition-all duration-300
        ${isSelected
          ? 'ring-2 ring-neutral-900 border-transparent shadow-xl'
          : 'shadow-soft hover:shadow-premium hover:border-neutral-200'
        }
      `}
    >
      {/* Selection checkbox */}
      {onSelect && (
        <button
          onClick={() => onSelect(lead.id)}
          className={`
            absolute top-6 right-6 w-5 h-5 rounded-full border transition-all flex items-center justify-center z-10
            ${isSelected
              ? 'bg-neutral-900 border-neutral-900'
              : 'bg-white border-neutral-200 hover:border-neutral-900'
            }
          `}
        >
          {isSelected && <Check className="w-3 h-3 text-white" strokeWidth={4} />}
        </button>
      )}

      <div className="p-6">
        {/* Business Header */}
        <div className="flex items-start gap-5 mb-6">
          <div className="flex-shrink-0 w-12 h-12 bg-neutral-900 rounded-2xl flex items-center justify-center shadow-lg shadow-black/5">
            <Building2 className="w-6 h-6 text-white" />
          </div>

          <div className="flex-1 min-w-0 pr-8">
            <h3 className="text-base font-black text-neutral-900 truncate tracking-tight">
              {lead.name}
            </h3>
            <div className="flex items-center gap-1.5 mt-1">
              <MapPin className="w-3.5 h-3.5 text-neutral-400" />
              <span className="text-[11px] font-bold text-neutral-500 truncate">
                {lead.address}
              </span>
            </div>

            {/* Rating */}
            {lead.rating > 0 && (
              <div className="flex items-center gap-3 mt-2.5">
                <div className="flex items-center gap-1 px-1.5 py-0.5 bg-amber-50 rounded-lg">
                  <Star className="w-3 h-3 text-amber-500 fill-current" />
                  <span className="text-[10px] font-black text-amber-900">
                    {lead.rating.toFixed(1)}
                  </span>
                </div>
                <span className="text-[10px] font-black text-neutral-300 uppercase tracking-widest">
                  {lead.user_ratings_total} Reviews
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Tags - Cleaner Badges */}
        <div className="flex flex-wrap gap-2 mb-6">
          {hasCeoEmail && (
            <span className="px-3 py-1 text-[10px] font-black bg-emerald-50 text-emerald-700 rounded-full flex items-center gap-1.5 uppercase tracking-wider shadow-sm">
              <div className="w-1 h-1 bg-emerald-500 rounded-full" /> CEO Email
            </span>
          )}
          {hasLinkedIn && (
            <span className="px-3 py-1 text-[10px] font-black bg-blue-50 text-blue-700 rounded-full flex items-center gap-1.5 uppercase tracking-wider shadow-sm">
              <div className="w-1 h-1 bg-blue-500 rounded-full" /> LinkedIn
            </span>
          )}
          {!hasCeoEmail && lead.email && (
            <span className="px-3 py-1 text-[10px] font-black bg-neutral-100 text-neutral-500 rounded-full uppercase tracking-wider">
              Generic Mail
            </span>
          )}
        </div>

        {/* Decision Maker Section - Simplified */}
        {lead.decision_maker && (
          <div className="bg-neutral-50 rounded-2xl p-5 mb-4 border border-neutral-100 group-hover:bg-neutral-900 transition-colors group/dm">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center shadow-sm group-hover/dm:bg-white/10">
                <User className="w-5 h-5 text-neutral-400 group-hover/dm:text-white" />
              </div>
              <div>
                <p className="font-black text-sm text-neutral-900 group-hover/dm:text-white transition-colors">
                  {lead.decision_maker.full_name || 'Unknown'}
                </p>
                <p className="text-[10px] text-neutral-400 font-bold uppercase tracking-widest group-hover/dm:text-white/50">
                  {lead.decision_maker.job_title || 'Decision Maker'}
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {lead.decision_maker.email && (
                <ContactRow
                  icon={Mail}
                  value={lead.decision_maker.email}
                  onCopy={() => handleCopy(lead.decision_maker!.email, 'email')}
                  isCopied={copiedField === 'email'}
                  inverse={true}
                />
              )}
              {lead.decision_maker.linkedin_url && (
                <ContactRow
                  icon={Linkedin}
                  value="View Profile"
                  href={lead.decision_maker.linkedin_url}
                  inverse={true}
                />
              )}
            </div>
          </div>
        )}

        {/* Expand/Collapse */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-between px-3 py-2 text-[10px] font-black uppercase tracking-[0.2em] text-neutral-400 hover:text-neutral-900 transition-all border-t border-neutral-50 mt-2"
        >
          <span>{isExpanded ? 'Collapse Intel' : 'Show Entity Intel'}</span>
          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown className="w-4 h-4" />
          </motion.div>
        </button>

        {/* Expanded Content */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="pt-4 space-y-3">
                {lead.phone && (
                  <ContactRow
                    icon={Phone}
                    value={lead.phone}
                    onCopy={() => handleCopy(lead.phone, 'phone')}
                    isCopied={copiedField === 'phone'}
                  />
                )}
                {lead.website && (
                  <ContactRow
                    icon={Globe}
                    value={extractDomain(lead.website)}
                    href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`}
                  />
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

interface ContactRowProps {
  icon: React.ElementType;
  value: string;
  label?: string;
  href?: string;
  onCopy?: () => void;
  isCopied?: boolean;
  inverse?: boolean;
}

function ContactRow({ icon: Icon, value, label, href, onCopy, isCopied, inverse }: ContactRowProps) {
  return (
    <div className={`flex items-center justify-between gap-2 group/row p-2 rounded-xl transition-colors ${inverse ? 'hover:bg-white/10' : 'hover:bg-neutral-50'}`}>
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <Icon className={`w-4 h-4 flex-shrink-0 ${inverse ? 'text-white/40' : 'text-neutral-400'}`} />
        <span className={`text-[11px] font-bold truncate ${inverse ? 'text-white/80' : 'text-neutral-600'}`}>{value}</span>
      </div>

      <div className="flex items-center gap-2">
        {onCopy && (
          <button
            onClick={onCopy}
            className={`p-1.5 rounded-lg transition-all ${inverse ? 'bg-white/10 text-white/40 hover:text-white hover:bg-white/20' : 'bg-neutral-100 text-neutral-400 hover:text-neutral-900 hover:bg-neutral-200'}`}
          >
            {isCopied ? (
              <Check className="w-3.5 h-3.5" />
            ) : (
              <Copy className="w-3.5 h-3.5" />
            )}
          </button>
        )}
        {href && (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className={`p-1.5 rounded-lg transition-all ${inverse ? 'bg-white/10 text-white/40 hover:text-white hover:bg-white/20' : 'bg-neutral-100 text-neutral-400 hover:text-neutral-900 hover:bg-neutral-200'}`}
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        )}
      </div>
    </div>
  );
}

export function LeadCardSkeleton() {
  return (
    <div className="bg-white border border-neutral-100 rounded-[28px] p-6 space-y-6 shadow-soft">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 bg-neutral-50 rounded-2xl animate-pulse" />
        <div className="flex-1 space-y-2">
          <div className="h-5 w-48 bg-neutral-100 rounded-lg animate-pulse" />
          <div className="h-4 w-32 bg-neutral-50 rounded-lg animate-pulse" />
        </div>
      </div>
      <div className="h-24 bg-neutral-50 rounded-2xl animate-pulse" />
      <div className="h-10 bg-neutral-50 rounded-xl animate-pulse" />
    </div>
  );
}
