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
        group relative bg-[var(--color-surface)] border rounded-2xl overflow-hidden transition-all duration-300
        ${isSelected
          ? 'border-[var(--color-brand-purple)] shadow-lg shadow-[var(--color-brand-purple)]/10'
          : 'border-[var(--color-border)] hover:border-[var(--color-border-light)]'
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
            absolute top-4 right-4 w-6 h-6 rounded-md border-2 flex items-center justify-center transition-all
            ${isSelected
              ? 'bg-[var(--color-brand-purple)] border-[var(--color-brand-purple)]'
              : 'border-[var(--color-border)] hover:border-[var(--color-brand-purple)]'
            }
          `}
        >
          {isSelected && <Check className="w-4 h-4 text-white" strokeWidth={3} />}
        </motion.button>
      )}

      <div className="p-5">
        {/* Business Header */}
        <div className="flex items-start gap-4 mb-4">
          {/* Company icon */}
          <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-[var(--color-brand-purple)]/20 to-[var(--color-brand-blue)]/20 rounded-xl flex items-center justify-center border border-[var(--color-border)]">
            <Building2 className="w-6 h-6 text-[var(--color-brand-purple)]" />
          </div>

          <div className="flex-1 min-w-0 pr-8">
            <h3 className="font-[family-name:var(--font-display)] text-lg font-semibold text-[var(--color-text-primary)] truncate">
              {lead.name}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <MapPin className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
              <span className="text-sm text-[var(--color-text-secondary)] truncate">
                {lead.address}
              </span>
            </div>

            {/* Rating */}
            {lead.rating > 0 && (
              <div className="flex items-center gap-2 mt-2">
                <div className="flex items-center gap-1">
                  <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                  <span className="text-sm font-semibold text-[var(--color-text-primary)]">
                    {lead.rating.toFixed(1)}
                  </span>
                </div>
                <span className="text-xs text-[var(--color-text-muted)]">
                  ({lead.user_ratings_total} reviews)
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-2 mb-4">
          {hasCeoEmail && (
            <span className="badge badge-success">
              <Check className="w-3 h-3" /> CEO Email
            </span>
          )}
          {hasLinkedIn && (
            <span className="badge badge-info">
              <Linkedin className="w-3 h-3" /> LinkedIn
            </span>
          )}
          {!hasCeoEmail && lead.email && (
            <span className="badge badge-warning">
              Business Email
            </span>
          )}
        </div>

        {/* Decision Maker Section */}
        {lead.decision_maker && (
          <div className="bg-[var(--color-abyss)] rounded-xl p-4 border border-[var(--color-border)] mb-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-gradient-to-br from-[var(--color-brand-cyan)]/20 to-[var(--color-brand-blue)]/20 rounded-full flex items-center justify-center">
                <User className="w-5 h-5 text-[var(--color-brand-cyan)]" />
              </div>
              <div>
                <p className="font-medium text-[var(--color-text-primary)]">
                  {lead.decision_maker.full_name || 'Unknown'}
                </p>
                <p className="text-xs text-[var(--color-text-muted)]">
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
          className="w-full flex items-center justify-center gap-2 py-2 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors"
        >
          <span>{isExpanded ? 'Less details' : 'More details'}</span>
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
              <div className="pt-4 border-t border-[var(--color-border)] space-y-3">
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
        <Icon className="w-4 h-4 text-[var(--color-text-muted)] flex-shrink-0" />
        {label && (
          <span className="text-xs text-[var(--color-text-muted)] flex-shrink-0">{label}:</span>
        )}
        <span className="text-sm text-[var(--color-text-secondary)] truncate">{value}</span>
      </div>

      <div className="flex items-center gap-1 opacity-0 group-hover/row:opacity-100 transition-opacity">
        {onCopy && (
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={onCopy}
            className="p-1.5 rounded-md hover:bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:text-[var(--color-brand-purple)] transition-colors"
          >
            {isCopied ? (
              <Check className="w-3.5 h-3.5 text-[var(--color-success)]" />
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
            className="p-1.5 rounded-md hover:bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:text-[var(--color-brand-blue)] transition-colors"
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
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-5">
      <div className="flex items-start gap-4 mb-4">
        <div className="w-12 h-12 skeleton rounded-xl" />
        <div className="flex-1 space-y-2">
          <div className="h-5 w-48 skeleton" />
          <div className="h-4 w-64 skeleton" />
          <div className="h-4 w-24 skeleton" />
        </div>
      </div>
      <div className="flex gap-2 mb-4">
        <div className="h-6 w-24 skeleton rounded-full" />
        <div className="h-6 w-20 skeleton rounded-full" />
      </div>
      <div className="bg-[var(--color-abyss)] rounded-xl p-4 space-y-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 skeleton rounded-full" />
          <div className="space-y-1.5">
            <div className="h-4 w-32 skeleton" />
            <div className="h-3 w-20 skeleton" />
          </div>
        </div>
        <div className="h-4 w-full skeleton" />
        <div className="h-4 w-3/4 skeleton" />
      </div>
    </div>
  );
}
