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
        group relative bg-white dark:bg-white border-2 overflow-hidden transition-all duration-300
        ${isSelected
          ? 'border-black dark:border-black shadow-none ring-2 ring-black ring-offset-2'
          : 'border-neutral-200 dark:border-neutral-200 hover:border-black dark:hover:border-black'
        }
      `}
    >
      {/* Selection checkbox */}
      {onSelect && (
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => onSelect(lead.id)}
          className={`
            absolute top-4 right-4 w-6 h-6 border-2 flex items-center justify-center transition-all
            ${isSelected
              ? 'bg-black dark:bg-black border-black dark:border-black'
              : 'bg-white dark:bg-white border-black dark:border-black hover:bg-neutral-50'
            }
          `}
        >
          {isSelected && <Check className="w-4 h-4 text-white dark:text-white" strokeWidth={3} />}
        </motion.button>
      )}

      <div className="p-5">
        {/* Business Header */}
        <div className="flex items-start gap-4 mb-4">
          {/* Company icon */}
          <div className="flex-shrink-0 w-12 h-12 bg-white dark:bg-white border-2 border-black dark:border-black flex items-center justify-center group-hover:translate-x-[2px] group-hover:translate-y-[2px] transition-transform">
            <Building2 className="w-6 h-6 text-black dark:text-black" />
          </div>

          <div className="flex-1 min-w-0 pr-8">
            <h3 className="text-lg font-black uppercase tracking-tighter text-black dark:text-black truncate font-mono">
              {lead.name}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <MapPin className="w-3.5 h-3.5 text-neutral-400" />
              <span className="text-[10px] font-bold uppercase tracking-widest text-neutral-500 truncate font-mono">
                {lead.address}
              </span>
            </div>

            {/* Rating */}
            {lead.rating > 0 && (
              <div className="flex items-center gap-2 mt-2">
                <div className="flex items-center gap-1">
                  <Star className="w-4 h-4 text-black dark:text-black fill-current" />
                  <span className="text-xs font-black text-black dark:text-black font-mono">
                    {lead.rating.toFixed(1)}
                  </span>
                </div>
                <span className="text-[9px] font-bold text-neutral-400 uppercase tracking-widest font-mono">
                  {lead.user_ratings_total}_REVIEWS
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-2 mb-4">
          {hasCeoEmail && (
            <span className="px-2 py-1 text-[9px] uppercase font-black bg-black text-white dark:bg-black dark:text-white flex items-center gap-1 font-mono">
              <Check className="w-3 h-3" /> CEO_EMAIL
            </span>
          )}
          {hasLinkedIn && (
            <span className="px-2 py-1 text-[9px] uppercase font-black border-2 border-black dark:border-black text-black dark:text-black flex items-center gap-1 font-mono">
              <Linkedin className="w-3 h-3" /> LINKEDIN
            </span>
          )}
          {!hasCeoEmail && lead.email && (
            <span className="px-2 py-1 text-[9px] uppercase font-black bg-neutral-100 dark:bg-neutral-100 text-neutral-600 dark:text-neutral-600 font-mono">
              BUSINESS_MAIL
            </span>
          )}
        </div>

        {/* Decision Maker Section */}
        {lead.decision_maker && (
          <div className="bg-neutral-50 dark:bg-neutral-50 p-4 border-2 border-black dark:border-black mb-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-black dark:bg-black flex items-center justify-center">
                <User className="w-5 h-5 text-white dark:text-white" />
              </div>
              <div>
                <p className="font-black uppercase text-xs tracking-tighter text-black dark:text-black font-mono">
                  {lead.decision_maker.full_name || 'Unknown'}
                </p>
                <p className="text-[9px] text-neutral-500 uppercase font-black tracking-widest font-mono">
                  {lead.decision_maker.job_title || 'Decision Maker'}
                </p>
              </div>
            </div>

            {/* Contact Info */}
            <div className="space-y-2">
              {lead.decision_maker.email && (
                <ContactRow
                  icon={Mail}
                  value={lead.decision_maker.email}
                  onCopy={() => handleCopy(lead.decision_maker!.email, 'email')}
                  isCopied={copiedField === 'email'}
                />
              )}
              {lead.decision_maker.linkedin_url && (
                <ContactRow
                  icon={Linkedin}
                  value={lead.decision_maker.linkedin_url.replace('https://linkedin.com/in/', '')}
                  href={lead.decision_maker.linkedin_url}
                />
              )}
            </div>
          </div>
        )}

        {/* Expand/Collapse Button */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-center gap-2 py-2 text-[10px] font-black uppercase tracking-widest text-neutral-400 hover:text-black dark:hover:text-black transition-colors font-mono"
        >
          <span>{isExpanded ? 'LESS_ENTITY_INTEL' : 'VIEW_ENTITY_INTEL'}</span>
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
              <div className="pt-4 border-t-2 border-neutral-100 dark:border-neutral-100 space-y-3">
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
                {lead.email && lead.email !== lead.decision_maker?.email && (
                  <ContactRow
                    icon={Mail}
                    value={lead.email}
                    label="Business"
                    onCopy={() => handleCopy(lead.email, 'businessEmail')}
                    isCopied={copiedField === 'businessEmail'}
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
}

function ContactRow({ icon: Icon, value, label, href, onCopy, isCopied }: ContactRowProps) {
  return (
    <div className="flex items-center justify-between gap-2 group/row">
      <div className="flex items-center gap-2 min-w-0 flex-1">
        <Icon className="w-4 h-4 text-neutral-400 flex-shrink-0" />
        {label && (
          <span className="text-[10px] font-black uppercase tracking-widest text-neutral-400 flex-shrink-0 font-mono">{label}:</span>
        )}
        <span className="text-[10px] font-bold text-neutral-600 uppercase tracking-tight truncate font-mono">{value}</span>
      </div>

      <div className="flex items-center gap-1 opacity-0 group-hover/row:opacity-100 transition-opacity">
        {onCopy && (
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={onCopy}
            className="p-1.5 border-2 border-transparent hover:border-black dark:hover:border-black text-neutral-400 hover:text-black dark:hover:text-black transition-colors"
          >
            {isCopied ? (
              <Check className="w-3.5 h-3.5 text-black dark:text-black" />
            ) : (
              <Copy className="w-3.5 h-3.5" />
            )}
          </motion.button>
        )}
        {href && (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1.5 border-2 border-transparent hover:border-black dark:hover:border-black text-neutral-400 hover:text-black dark:hover:text-black transition-colors"
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        )}
      </div>
    </div>
  );
}

// Skeleton version
export function LeadCardSkeleton() {
  return (
    <div className="bg-white dark:bg-white border-2 border-neutral-100 dark:border-neutral-100 p-5 space-y-4">
      <div className="flex items-start gap-4 mb-4">
        <div className="w-12 h-12 bg-neutral-50 dark:bg-neutral-50 border-2 border-neutral-100 dark:border-neutral-100" />
        <div className="flex-1 space-y-2">
          <div className="h-5 w-48 bg-neutral-100 dark:bg-neutral-100" />
          <div className="h-4 w-64 bg-neutral-50 dark:bg-neutral-50" />
          <div className="h-4 w-24 bg-neutral-50 dark:bg-neutral-50" />
        </div>
      </div>
      <div className="flex gap-2 mb-4">
        <div className="h-6 w-24 bg-neutral-100 dark:bg-neutral-100" />
        <div className="h-6 w-20 bg-neutral-100 dark:bg-neutral-100" />
      </div>
      <div className="bg-neutral-50 dark:bg-neutral-50 border-2 border-neutral-100 dark:border-neutral-100 p-4 space-y-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-neutral-100 dark:bg-neutral-100" />
          <div className="space-y-1.5">
            <div className="h-4 w-32 bg-neutral-100 dark:bg-neutral-100" />
            <div className="h-3 w-20 bg-neutral-100 dark:bg-neutral-100" />
          </div>
        </div>
        <div className="h-4 w-full bg-neutral-100 dark:bg-neutral-100" />
        <div className="h-4 w-3/4 bg-neutral-100 dark:bg-neutral-100" />
      </div>
    </div>
  );
}
