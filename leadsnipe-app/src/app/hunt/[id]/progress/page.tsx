'use client';

import { useState, useEffect, useCallback, use } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'motion/react';
import {
  ArrowLeft,
  Target,
  MapPin,
  Users,
  Clock,
  ArrowRight,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import { ProgressTracker, ActivityFeed } from '@/components';
import type { HuntProgress, ActivityEvent, HuntDetails } from '@/lib/types';
import { formatDuration } from '@/lib/utils';
import { v4 as uuidv4 } from 'uuid';

interface PageProps {
  params: Promise<{ id: string }>;
}

import { api } from '@/lib/api';

// ... (other imports)

export default function HuntProgressPage({ params }: PageProps) {
  const { id: huntId } = use(params);
  const router = useRouter();

  const [huntDetails, setHuntDetails] = useState<HuntDetails | null>(null);
  const [progress, setProgress] = useState<HuntProgress>({
    stage: 1,
    stage_name: 'Initializing...',
    percentage: 0,
    processed: 0,
    total: 0,
    elapsed_time: 0,
    estimated_total: 120,
  });
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [status, setStatus] = useState<'running' | 'completed' | 'failed'>('running');
  const [stageTimes, setStageTimes] = useState<Record<string, number>>({});
  const [error, setError] = useState<string | null>(null);

  // Add event helper
  const addEvent = useCallback((type: ActivityEvent['type'], message: string) => {
    setEvents(prev => [...prev, {
      id: uuidv4(),
      timestamp: new Date().toISOString(),
      type,
      message,
    }]);
  }, []);

  // Poll for hunt status/progress
  useEffect(() => {
    let interval: NodeJS.Timeout;

    async function checkStatus() {
      try {
        const data = await api.getHuntDetails(huntId);
        setHuntDetails(data);
        if (data.progress) setProgress(data.progress);

        if (data.status === 'completed') {
          setStatus('completed');
          clearInterval(interval);
        } else if (data.status === 'failed') {
          setStatus('failed');
          // setError(data.error); // HuntDetails type doesn't have error field yet?
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }

    checkStatus(); // Initial check
    if (status === 'running') {
      interval = setInterval(checkStatus, 2000);
    }

    return () => clearInterval(interval);
  }, [huntId, status]);

  // SSE for real-time logs
  useEffect(() => {
    if (status !== 'running') return;

    // Connect to backend stream
    const eventSource = new EventSource(`http://127.0.0.1:8000/api/hunt/${huntId}/logs`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Backend sends: { id, timestamp, level, message } OR { type: 'complete', ... }
        if (data.type === 'complete') {
          // Polling handles completion, but we can close stream here
          eventSource.close();
        } else if (data.message) {
          const type = data.level === 'ERROR' ? 'error' : data.level === 'WARN' ? 'warning' : 'info';
          addEvent(type, data.message);
        }
      } catch (err) {
        console.error('Failed to parse SSE data:', err);
      }
    };

    eventSource.onerror = () => {
      // console.error('SSE connection error');
      // eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [huntId, status, addEvent]);

  return (
    <div className="min-h-screen py-12 px-6">
      <div className="max-w-4xl mx-auto">
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

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center gap-4 mb-4">
            <div className={`
              w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg
              ${status === 'running'
                ? 'bg-black dark:bg-white'
                : status === 'completed'
                  ? 'bg-neutral-100 dark:bg-neutral-800'
                  : 'border-2 border-black dark:border-white'
              }
            `}>
              {status === 'running' ? (
                <Target className="w-7 h-7 text-white dark:text-black" />
              ) : status === 'completed' ? (
                <CheckCircle2 className="w-7 h-7 text-black dark:text-white" />
              ) : (
                <XCircle className="w-7 h-7 text-black dark:text-white" />
              )}
            </div>
            <div>
              <h1 className="font-[family-name:var(--font-display)] text-2xl font-bold text-black dark:text-white">
                {status === 'running'
                  ? 'Lead Hunt in Progress'
                  : status === 'completed'
                    ? 'Hunt Completed!'
                    : 'Hunt Failed'
                }
              </h1>
              {huntDetails && (
                <div className="flex items-center gap-4 text-sm text-neutral-500 font-medium mt-1">
                  <span className="flex items-center gap-1">
                    <Target className="w-3.5 h-3.5" />
                    {huntDetails.industry}
                  </span>
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5" />
                    {huntDetails.location}
                  </span>
                  <span className="flex items-center gap-1">
                    <Users className="w-3.5 h-3.5" />
                    {huntDetails.target} leads
                  </span>
                </div>
              )}
            </div>
          </div>
        </motion.div>

        {/* Main Content */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Progress Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white dark:bg-black border border-neutral-200 dark:border-neutral-800 rounded-2xl p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="font-bold text-black dark:text-white uppercase tracking-tight">
                Progress
              </h2>
              <div className="flex items-center gap-2 text-sm text-neutral-500 font-bold">
                <Clock className="w-4 h-4" />
                <span>{formatDuration(progress.elapsed_time)}</span>
              </div>
            </div>

            <ProgressTracker progress={progress} stageTimes={stageTimes} />

            {/* Completion Actions */}
            {status === 'completed' && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6 pt-6 border-t border-neutral-200 dark:border-neutral-800"
              >
                <Link href={`/hunt/${huntId}/results`}>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="w-full flex items-center justify-center gap-3 py-4 px-6 bg-black dark:bg-white rounded-xl font-bold text-white dark:text-black shadow-lg"
                  >
                    <span>View Results</span>
                    <ArrowRight className="w-5 h-5" />
                  </motion.button>
                </Link>
              </motion.div>
            )}

            {/* Error State */}
            {status === 'failed' && error && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6 pt-6 border-t border-[var(--color-border)]"
              >
                <div className="p-4 bg-[var(--color-error)]/10 border border-[var(--color-error)]/30 rounded-xl">
                  <p className="text-sm text-[var(--color-error)]">{error}</p>
                </div>
                <Link href="/hunt/new" className="block mt-4">
                  <button className="w-full py-3 px-6 bg-[var(--color-elevated)] border border-[var(--color-border)] rounded-xl font-medium text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors">
                    Try Again
                  </button>
                </Link>
              </motion.div>
            )}
          </motion.div>

          {/* Activity Feed */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <ActivityFeed events={events} maxHeight="400px" />
          </motion.div>
        </div>
      </div>
    </div>
  );
}
