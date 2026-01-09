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

export default function HuntProgressPage({ params }: PageProps) {
  const { id: huntId } = use(params);
  const router = useRouter();

  const [huntDetails, setHuntDetails] = useState<HuntDetails | null>(null);
  const [progress, setProgress] = useState<HuntProgress>({
    stage: 1,
    stage_name: 'Google Maps Scraping',
    percentage: 0,
    processed: 0,
    total: 0,
    elapsed_time: 0,
    estimated_total: 120,
  });
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [status, setStatus] = useState<'running' | 'completed' | 'failed'>('running');
  const [stageTimes, setStageTimes] = useState<{
    stage1?: number;
    stage2?: number;
    stage3?: number;
  }>({});
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

  // Fetch hunt details
  useEffect(() => {
    async function fetchHuntDetails() {
      try {
        const response = await fetch(`/api/hunt/${huntId}/status`);
        if (response.ok) {
          const data = await response.json();
          setHuntDetails(data);

          if (data.progress) {
            setProgress(data.progress);
          }

          if (data.status === 'completed') {
            setStatus('completed');
          } else if (data.status === 'failed') {
            setStatus('failed');
            setError(data.error || 'Hunt failed');
          }
        }
      } catch (err) {
        console.error('Failed to fetch hunt details:', err);
      }
    }

    fetchHuntDetails();
  }, [huntId]);

  // SSE for real-time updates
  useEffect(() => {
    if (status !== 'running') return;

    const eventSource = new EventSource(`/api/hunt/${huntId}/stream`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'progress') {
          setProgress(data.progress);

          // Update stage times
          if (data.stage_times) {
            setStageTimes(data.stage_times);
          }
        } else if (data.type === 'event') {
          addEvent(data.event_type || 'info', data.message);
        } else if (data.type === 'completed') {
          setStatus('completed');
          addEvent('success', 'Hunt completed successfully!');
          eventSource.close();
        } else if (data.type === 'failed') {
          setStatus('failed');
          setError(data.error || 'Hunt failed');
          addEvent('error', data.error || 'Hunt failed');
          eventSource.close();
        }
      } catch (err) {
        console.error('Failed to parse SSE data:', err);
      }
    };

    eventSource.onerror = () => {
      console.error('SSE connection error');
      // Don't close immediately, let it retry
    };

    return () => {
      eventSource.close();
    };
  }, [huntId, status, addEvent]);

  // Simulate progress for demo if no real backend
  useEffect(() => {
    if (!huntDetails) return;
    if (status !== 'running') return;

    // Add initial events
    addEvent('info', `Starting hunt for ${huntDetails.industry} in ${huntDetails.location}`);
    addEvent('info', `Target: ${huntDetails.target} leads`);

    // Simulate progress
    const stages = [
      { stage: 1, name: 'Google Maps Scraping', duration: 3000, messages: ['Generating search queries...', 'Scraping Google Maps...', 'Found businesses'] },
      { stage: 2, name: 'Decision Maker Finding', duration: 5000, messages: ['Finding CEO emails...', 'Processing domains...', 'Validating emails'] },
      { stage: 3, name: 'LinkedIn Discovery', duration: 2000, messages: ['Searching LinkedIn profiles...', 'Parsing websites...', 'Completing search'] },
    ];

    let currentStage = 0;
    let stageProgress = 0;
    let totalElapsed = 0;

    const interval = setInterval(() => {
      if (currentStage >= stages.length) {
        setStatus('completed');
        addEvent('success', 'Hunt completed successfully!');
        clearInterval(interval);
        return;
      }

      const stage = stages[currentStage];
      stageProgress += 10;
      totalElapsed += 500;

      // Random events
      if (Math.random() > 0.7) {
        const msgIndex = Math.floor(Math.random() * stage.messages.length);
        addEvent('info', stage.messages[msgIndex]);
      }

      if (Math.random() > 0.85) {
        addEvent('success', `Found CEO: ${['John Smith', 'Jane Doe', 'Mike Johnson', 'Sarah Williams'][Math.floor(Math.random() * 4)]}`);
      }

      const overallProgress = Math.min(
        Math.round(((currentStage * 100) + stageProgress) / 3),
        100
      );

      setProgress({
        stage: (currentStage + 1) as 1 | 2 | 3,
        stage_name: stage.name,
        percentage: overallProgress,
        processed: Math.round((overallProgress / 100) * (huntDetails.target || 25)),
        total: huntDetails.target || 25,
        elapsed_time: totalElapsed / 1000,
        estimated_total: 120,
      });

      if (stageProgress >= 100) {
        setStageTimes(prev => ({
          ...prev,
          [`stage${currentStage + 1}`]: totalElapsed / 1000,
        }));
        addEvent('success', `Stage ${currentStage + 1} completed`);
        currentStage++;
        stageProgress = 0;
      }
    }, 500);

    return () => clearInterval(interval);
  }, [huntDetails, status, addEvent]);

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
                ? 'bg-gradient-to-br from-[var(--color-brand-purple)] to-[var(--color-brand-blue)] shadow-[var(--color-brand-purple)]/20 animate-pulse-glow'
                : status === 'completed'
                  ? 'bg-[var(--color-success)]'
                  : 'bg-[var(--color-error)]'
              }
            `}>
              {status === 'running' ? (
                <Target className="w-7 h-7 text-white" />
              ) : status === 'completed' ? (
                <CheckCircle2 className="w-7 h-7 text-white" />
              ) : (
                <XCircle className="w-7 h-7 text-white" />
              )}
            </div>
            <div>
              <h1 className="font-[family-name:var(--font-display)] text-2xl font-bold text-[var(--color-text-primary)]">
                {status === 'running'
                  ? 'Lead Hunt in Progress'
                  : status === 'completed'
                    ? 'Hunt Completed!'
                    : 'Hunt Failed'
                }
              </h1>
              {huntDetails && (
                <div className="flex items-center gap-4 text-sm text-[var(--color-text-muted)] mt-1">
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
            className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="font-semibold text-[var(--color-text-primary)]">
                Progress
              </h2>
              <div className="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
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
                className="mt-6 pt-6 border-t border-[var(--color-border)]"
              >
                <Link href={`/hunt/${huntId}/results`}>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="w-full flex items-center justify-center gap-3 py-4 px-6 bg-gradient-to-r from-[var(--color-brand-purple)] to-[var(--color-brand-blue)] rounded-xl font-semibold text-white shadow-lg shadow-[var(--color-brand-purple)]/25"
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
