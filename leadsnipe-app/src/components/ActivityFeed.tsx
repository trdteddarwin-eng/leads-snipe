'use client';

import { useEffect, useRef } from 'react';
import { motion } from 'motion/react';
import { CheckCircle2, Info, AlertTriangle, XCircle, Search } from 'lucide-react';
import type { ActivityEvent } from '@/lib/types';
import { formatTime } from '@/lib/utils';

interface ActivityFeedProps {
  events: ActivityEvent[];
  maxHeight?: string;
  autoScroll?: boolean;
}

export function ActivityFeed({ events, maxHeight = '300px', autoScroll = true }: ActivityFeedProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events, autoScroll]);

  const getEventConfig = (type: ActivityEvent['type']) => {
    switch (type) {
      case 'success':
        return {
          icon: CheckCircle2,
          color: 'text-[var(--color-success)]',
          borderColor: 'border-l-[var(--color-success)]',
          bgColor: 'bg-[var(--color-success)]/5',
        };
      case 'warning':
        return {
          icon: AlertTriangle,
          color: 'text-[var(--color-warning)]',
          borderColor: 'border-l-[var(--color-warning)]',
          bgColor: 'bg-[var(--color-warning)]/5',
        };
      case 'error':
        return {
          icon: XCircle,
          color: 'text-[var(--color-error)]',
          borderColor: 'border-l-[var(--color-error)]',
          bgColor: 'bg-[var(--color-error)]/5',
        };
      default:
        return {
          icon: Info,
          color: 'text-[var(--color-brand-blue)]',
          borderColor: 'border-l-[var(--color-brand-blue)]',
          bgColor: 'bg-[var(--color-brand-blue)]/5',
        };
    }
  };

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-[var(--color-border)] bg-[var(--color-abyss)]">
        <div className="flex items-center gap-2">
          <Search className="w-4 h-4 text-[var(--color-brand-purple)]" />
          <h3 className="font-semibold text-[var(--color-text-primary)]">Live Activity</h3>
          <span className="ml-auto text-xs text-[var(--color-text-muted)]">
            {events.length} events
          </span>
        </div>
      </div>

      {/* Events */}
      <div
        ref={scrollRef}
        className="overflow-y-auto"
        style={{ maxHeight }}
      >
        {events.length === 0 ? (
          <div className="px-5 py-8 text-center text-[var(--color-text-muted)] text-sm">
            Waiting for activity...
          </div>
        ) : (
          <div className="divide-y divide-[var(--color-border)]">
            {events.map((event, index) => {
              const config = getEventConfig(event.type);
              const Icon = config.icon;

              return (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.02 }}
                  className={`
                    px-5 py-3 flex items-start gap-3 border-l-2 hover:${config.bgColor} transition-colors
                    ${config.borderColor}
                  `}
                >
                  <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${config.color}`} />

                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-[var(--color-text-secondary)] break-words">
                      {event.message}
                    </p>
                  </div>

                  <span className="flex-shrink-0 text-xs font-mono text-[var(--color-text-muted)]">
                    {formatTime(event.timestamp)}
                  </span>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>

      {/* Live indicator */}
      <div className="px-5 py-3 border-t border-[var(--color-border)] bg-[var(--color-abyss)] flex items-center gap-2">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--color-success)] opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--color-success)]"></span>
        </span>
        <span className="text-xs text-[var(--color-text-muted)]">Live updates</span>
      </div>
    </div>
  );
}
