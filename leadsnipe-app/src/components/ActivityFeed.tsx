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
          color: 'text-black',
          borderColor: 'border-l-black',
          bgColor: 'bg-neutral-50',
        };
      case 'warning':
        return {
          icon: AlertTriangle,
          color: 'text-neutral-600',
          borderColor: 'border-l-neutral-400',
          bgColor: 'bg-neutral-50',
        };
      case 'error':
        return {
          icon: XCircle,
          color: 'text-black',
          borderColor: 'border-l-black',
          bgColor: 'bg-neutral-100',
        };
      default:
        return {
          icon: Info,
          color: 'text-neutral-500',
          borderColor: 'border-l-neutral-200',
          bgColor: 'bg-neutral-50/50',
        };
    }
  };

  return (
    <div className="bg-white dark:bg-white border-2 border-black dark:border-black overflow-hidden shadow-none rounded-none">
      {/* Header */}
      <div className="px-5 py-4 border-b-2 border-black dark:border-black bg-white dark:bg-white">
        <div className="flex items-center gap-2">
          <Search className="w-4 h-4 text-black dark:text-black" />
          <h3 className="font-black text-black dark:text-black uppercase text-[10px] tracking-widest font-mono">Real-Time_Logs_v1.0</h3>
          <span className="ml-auto text-[9px] font-black text-neutral-400 uppercase font-mono">
            {events.length}_Events
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
          <div className="px-5 py-8 text-center text-neutral-400 text-[10px] font-black uppercase font-mono">
            Waiting_For_Sequence_Start...
          </div>
        ) : (
          <div className="divide-y-2 divide-neutral-100 dark:divide-neutral-100">
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
                    px-5 py-3 flex items-start gap-3 border-l-[3px] hover:bg-neutral-50 dark:hover:bg-neutral-50 transition-colors
                    ${event.type === 'success' ? 'border-l-black dark:border-l-black' :
                      event.type === 'error' ? 'border-l-black dark:border-l-black' :
                        'border-l-neutral-200 dark:border-l-neutral-200'}
                  `}
                >
                  <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 text-black dark:text-black`} />

                  <div className="flex-1 min-w-0">
                    <p className="text-[11px] text-neutral-600 dark:text-neutral-600 font-bold uppercase tracking-tight font-mono break-words">
                      {event.message}
                    </p>
                  </div>

                  <span className="flex-shrink-0 text-[9px] font-black font-mono text-neutral-400">
                    {formatTime(event.timestamp)}
                  </span>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>

      {/* Live indicator */}
      <div className="px-5 py-3 border-t-2 border-black dark:border-black bg-neutral-50 dark:bg-neutral-50 flex items-center gap-2">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-black dark:bg-black opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-black dark:bg-black"></span>
        </span>
        <span className="text-[9px] uppercase font-black text-neutral-500 tracking-widest font-mono">Streaming_Active</span>
      </div>
    </div>
  );
}
