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

        <div className="progress-bar h-3 bg-neutral-100 dark:bg-neutral-100 border-2 border-black dark:border-black rounded-none overflow-hidden">
          <motion.div
            className="h-full bg-black dark:bg-black"
            initial={{ width: 0 }}
            animate={{ width: `${progress.percentage}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
        </div>

        <div className="flex items-center justify-between text-xs text-neutral-400 font-bold uppercase tracking-tight">
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
                relative p-4 border-2 transition-all duration-300 rounded-none shadow-none
                ${stageStatus === 'active'
                  ? 'bg-neutral-50 dark:bg-neutral-50 border-black dark:border-black'
                  : stageStatus === 'completed'
                    ? 'bg-neutral-100 dark:bg-neutral-100 border-black dark:border-black'
                    : 'bg-white dark:bg-white border-neutral-200 dark:border-neutral-200 opacity-60'
                }
              `}
            >
              {/* Connector line */}
              {stage.id < 3 && (
                <div
                  className={`
                    absolute left-7 top-full w-[2px] h-3 -translate-x-1/2
                    ${stageStatus === 'completed'
                      ? 'bg-black dark:bg-black'
                      : 'bg-neutral-200 dark:bg-neutral-200'
                    }
                  `}
                />
              )}

              <div className="flex items-start gap-4">
                {/* Status Icon */}
                <div
                  className={`
                    flex-shrink-0 w-10 h-10 border-2 flex items-center justify-center
                    ${stageStatus === 'completed'
                      ? 'bg-black text-white dark:bg-black dark:text-white border-black dark:border-black'
                      : stageStatus === 'active'
                        ? 'bg-black text-white dark:bg-black dark:text-white border-black dark:border-black'
                        : 'bg-neutral-100 dark:bg-neutral-100 text-neutral-400 border-neutral-200 dark:border-neutral-200'
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
                        font-black uppercase text-[10px] tracking-widest font-mono
                        ${stageStatus === 'pending'
                          ? 'text-neutral-400'
                          : 'text-black dark:text-black'
                        }
                      `}
                    >
                      0{stage.id}_{stage.name}
                    </h4>

                    {/* Stage Status Badge */}
                    <span
                      className={`
                        text-[9px] uppercase font-black px-2 py-0.5 font-mono
                        ${stageStatus === 'completed'
                          ? 'bg-neutral-200 dark:bg-neutral-200 text-black dark:text-black'
                          : stageStatus === 'active'
                            ? 'bg-black text-white dark:bg-black dark:text-white'
                            : 'bg-neutral-100 dark:bg-neutral-100 text-neutral-400'
                        }
                      `}
                    >
                      {stageStatus === 'completed' ? 'Complete' : stageStatus === 'active' ? 'Scanning' : 'Waiting'}
                    </span>
                  </div>

                  <p className="text-[10px] text-neutral-500 font-bold uppercase tracking-tight mt-1 font-mono">
                    {stage.description}
                  </p>

                  {/* Stage metrics */}
                  {(stageStatus === 'completed' || stageStatus === 'active') && (
                    <div className="flex items-center gap-4 mt-2 text-[10px]">
                      {stageTime !== undefined && (
                        <span className="text-neutral-400 font-mono font-black">
                          <Icon className="w-3 h-3 inline mr-1" />
                          {formatDuration(stageTime)}
                        </span>
                      )}
                      {stageStatus === 'active' && progress.stage === stage.id && (
                        <span className="font-black text-black dark:text-black animate-pulse font-mono">
                          PROCESSING_{progress.processed + 1}/{progress.total}
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
