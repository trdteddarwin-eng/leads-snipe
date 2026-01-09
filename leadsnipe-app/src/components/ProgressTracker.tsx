'use client';

import { motion } from 'motion/react';
import { Check, Loader2, Clock, MapPin, Mail, Linkedin } from 'lucide-react';
import type { HuntProgress } from '@/lib/types';
import { HUNT_STAGES } from '@/lib/types';
import { formatDuration } from '@/lib/utils';

interface ProgressTrackerProps {
  progress: HuntProgress;
  stageTimes?: {
    stage1?: number;
    stage2?: number;
    stage3?: number;
  };
}

export function ProgressTracker({ progress, stageTimes }: ProgressTrackerProps) {
  const stageIcons = {
    1: MapPin,
    2: Mail,
    3: Linkedin,
  };

  return (
    <div className="space-y-6">
      {/* Overall Progress */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-[var(--color-text-secondary)]">Overall Progress</span>
          <span className="font-mono font-semibold text-[var(--color-text-primary)]">
            {progress.percentage}%
          </span>
        </div>

        <div className="progress-bar h-3">
          <motion.div
            className="progress-bar-fill"
            initial={{ width: 0 }}
            animate={{ width: `${progress.percentage}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
        </div>

        <div className="flex items-center justify-between text-xs text-[var(--color-text-muted)]">
          <span>{progress.processed} / {progress.total} leads processed</span>
          <span>~{formatDuration(progress.estimated_total - progress.elapsed_time)} remaining</span>
        </div>
      </div>

      {/* Stage Indicators */}
      <div className="space-y-3">
        {HUNT_STAGES.map((stage) => {
          const Icon = stageIcons[stage.id as keyof typeof stageIcons];
          const stageStatus = getStageStatus(stage.id, progress.stage);
          const stageTime = stageTimes?.[`stage${stage.id}` as keyof typeof stageTimes];

          return (
            <motion.div
              key={stage.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: stage.id * 0.1 }}
              className={`
                relative p-4 rounded-xl border transition-all duration-300
                ${stageStatus === 'active'
                  ? 'bg-[var(--color-brand-purple)]/10 border-[var(--color-brand-purple)]/50'
                  : stageStatus === 'completed'
                    ? 'bg-[var(--color-success)]/5 border-[var(--color-success)]/30'
                    : 'bg-[var(--color-surface)] border-[var(--color-border)]'
                }
              `}
            >
              {/* Connector line */}
              {stage.id < 3 && (
                <div
                  className={`
                    absolute left-7 top-full w-0.5 h-3 -translate-x-1/2
                    ${stageStatus === 'completed'
                      ? 'bg-[var(--color-success)]'
                      : 'bg-[var(--color-border)]'
                    }
                  `}
                />
              )}

              <div className="flex items-start gap-4">
                {/* Status Icon */}
                <div
                  className={`
                    flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center
                    ${stageStatus === 'completed'
                      ? 'bg-[var(--color-success)] text-white'
                      : stageStatus === 'active'
                        ? 'bg-gradient-to-br from-[var(--color-brand-purple)] to-[var(--color-brand-blue)] text-white'
                        : 'bg-[var(--color-elevated)] text-[var(--color-text-muted)]'
                    }
                  `}
                >
                  {stageStatus === 'completed' ? (
                    <Check className="w-5 h-5" strokeWidth={3} />
                  ) : stageStatus === 'active' ? (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    >
                      <Loader2 className="w-5 h-5" />
                    </motion.div>
                  ) : (
                    <Clock className="w-5 h-5" />
                  )}
                </div>

                {/* Stage Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4
                      className={`
                        font-semibold
                        ${stageStatus === 'pending'
                          ? 'text-[var(--color-text-muted)]'
                          : 'text-[var(--color-text-primary)]'
                        }
                      `}
                    >
                      Stage {stage.id}: {stage.name}
                    </h4>

                    {/* Stage Status Badge */}
                    <span
                      className={`
                        text-xs font-semibold px-2 py-0.5 rounded-full
                        ${stageStatus === 'completed'
                          ? 'bg-[var(--color-success)]/20 text-[var(--color-success)]'
                          : stageStatus === 'active'
                            ? 'bg-[var(--color-brand-purple)]/20 text-[var(--color-brand-purple)]'
                            : 'bg-[var(--color-elevated)] text-[var(--color-text-muted)]'
                        }
                      `}
                    >
                      {stageStatus === 'completed' ? 'Complete' : stageStatus === 'active' ? 'In Progress' : 'Pending'}
                    </span>
                  </div>

                  <p className="text-sm text-[var(--color-text-muted)] mt-1">
                    {stage.description}
                  </p>

                  {/* Stage metrics */}
                  {(stageStatus === 'completed' || stageStatus === 'active') && (
                    <div className="flex items-center gap-4 mt-2 text-xs">
                      {stageTime !== undefined && (
                        <span className="text-[var(--color-text-secondary)]">
                          <Icon className="w-3 h-3 inline mr-1" />
                          {formatDuration(stageTime)}
                        </span>
                      )}
                      {stageStatus === 'active' && progress.stage === stage.id && (
                        <span className="text-[var(--color-brand-purple)]">
                          Processing lead {progress.processed + 1} of {progress.total}...
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

function getStageStatus(stageId: number, currentStage: number): 'completed' | 'active' | 'pending' {
  if (stageId < currentStage) return 'completed';
  if (stageId === currentStage) return 'active';
  return 'pending';
}

// Mini progress indicator for dashboard
export function ProgressMini({ progress }: { progress: HuntProgress }) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 progress-bar h-2">
        <motion.div
          className="progress-bar-fill"
          initial={{ width: 0 }}
          animate={{ width: `${progress.percentage}%` }}
        />
      </div>
      <span className="text-xs font-mono text-[var(--color-text-muted)] w-12">
        {progress.percentage}%
      </span>
    </div>
  );
}
