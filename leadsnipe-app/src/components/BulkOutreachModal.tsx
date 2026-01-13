'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
    X,
    Send,
    Loader2,
    CheckCircle,
    AlertCircle,
    Rocket,
    Clock,
    Sparkles,
    AlertTriangle,
} from 'lucide-react';
import type { Lead } from '@/lib/types';
import { api } from '@/lib/api';

interface BulkOutreachModalProps {
    leads: Lead[];
    isOpen: boolean;
    onClose: () => void;
    onComplete?: (results: SendResult[]) => void;
}

interface SendResult {
    leadId: string;
    leadName: string;
    status: 'pending' | 'sending' | 'success' | 'failed';
    error?: string;
}

interface VariableTag {
    key: string;
    label: string;
    description: string;
    icon?: React.ElementType;
}

const VARIABLE_TAGS: VariableTag[] = [
    { key: '{{owner_name}}', label: 'Owner Name', description: 'First name of the decision maker' },
    { key: '{{business_name}}', label: 'Business', description: 'Name of the business' },
    { key: '{{city}}', label: 'City', description: 'City from business address' },
    { key: '{{ai_insight}}', label: 'AI Insight', description: 'Auto-generated insight from analysis', icon: Sparkles },
];

const DAILY_LIMIT = 50;
const SEND_DELAY_MS = 3000;

export function BulkOutreachModal({ leads, isOpen, onClose, onComplete }: BulkOutreachModalProps) {
    // Template State
    const [subject, setSubject] = useState('Quick question about {{business_name}}');
    const [body, setBody] = useState(`Hi {{owner_name}},

I was looking at {{business_name}} and noticed:
{{ai_insight}}

Would love to chat about how we can help.

Best regards`);

    // Sending State
    const [isSending, setIsSending] = useState(false);
    const [sendResults, setSendResults] = useState<SendResult[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [showResults, setShowResults] = useState(false);

    const bodyRef = useRef<HTMLTextAreaElement>(null);
    const subjectRef = useRef<HTMLInputElement>(null);
    const lastFocusedRef = useRef<'subject' | 'body'>('body');

    // Reset state when opening
    useEffect(() => {
        if (isOpen) {
            setIsSending(false);
            setSendResults([]);
            setCurrentIndex(0);
            setShowResults(false);
        }
    }, [isOpen]);

    // Insert variable at cursor position
    const handleInsertVariable = (variable: string) => {
        const ref = lastFocusedRef.current === 'subject' ? subjectRef : bodyRef;
        const setValue = lastFocusedRef.current === 'subject' ? setSubject : setBody;
        const currentValue = lastFocusedRef.current === 'subject' ? subject : body;

        if (ref.current) {
            const start = ref.current.selectionStart || 0;
            const end = ref.current.selectionEnd || 0;
            const newValue = currentValue.substring(0, start) + variable + currentValue.substring(end);
            setValue(newValue);

            // Restore focus and cursor
            setTimeout(() => {
                ref.current?.focus();
                ref.current?.setSelectionRange(start + variable.length, start + variable.length);
            }, 0);
        } else {
            setValue(currentValue + variable);
        }
    };

    // Substitute variables for a specific lead
    const substituteVariables = (template: string, lead: Lead): string => {
        let result = template;

        // {{owner_name}} - First name of decision maker
        const ownerName = lead.decision_maker?.full_name?.split(' ')[0] || 'there';
        result = result.replace(/\{\{owner_name\}\}/g, ownerName);

        // {{business_name}}
        result = result.replace(/\{\{business_name\}\}/g, lead.name);

        // {{city}} - Extract from address
        const cityMatch = lead.address.match(/,\s*([^,]+),?\s*[A-Z]{2}/);
        const city = cityMatch ? cityMatch[1].trim() : lead.address.split(',')[0]?.trim() || 'your area';
        result = result.replace(/\{\{city\}\}/g, city);

        // {{ai_insight}} - Pull from quick_insights
        const insight = lead.quick_insights?.[0] || 'I noticed some opportunities for your business';
        result = result.replace(/\{\{ai_insight\}\}/g, insight);

        return result;
    };

    // Start the bulk send mission
    const handleStartMission = async () => {
        if (isSending || leads.length === 0) return;

        setIsSending(true);
        setShowResults(true);

        // Initialize results
        const initialResults: SendResult[] = leads.map(lead => ({
            leadId: lead.id,
            leadName: lead.name,
            status: 'pending',
        }));
        setSendResults(initialResults);

        // Send emails sequentially with delay
        for (let i = 0; i < leads.length; i++) {
            const lead = leads[i];
            setCurrentIndex(i);

            // Update status to sending
            setSendResults(prev => prev.map((r, idx) =>
                idx === i ? { ...r, status: 'sending' } : r
            ));

            try {
                const recipientEmail = lead.decision_maker?.email || lead.email;
                if (!recipientEmail) {
                    throw new Error('No email address');
                }

                const personalizedSubject = substituteVariables(subject, lead);
                const personalizedBody = substituteVariables(body, lead);

                const result = await api.sendEmail(recipientEmail, personalizedSubject, personalizedBody);

                if (result.success) {
                    setSendResults(prev => prev.map((r, idx) =>
                        idx === i ? { ...r, status: 'success' } : r
                    ));
                } else {
                    throw new Error(result.error || 'Failed to send');
                }
            } catch (error) {
                const errorMessage = error instanceof Error ? error.message : 'Unknown error';
                setSendResults(prev => prev.map((r, idx) =>
                    idx === i ? { ...r, status: 'failed', error: errorMessage } : r
                ));
            }

            // Delay before next email (except for last one)
            if (i < leads.length - 1) {
                await new Promise(resolve => setTimeout(resolve, SEND_DELAY_MS));
            }
        }

        setIsSending(false);
        onComplete?.(sendResults);
    };

    // Calculate progress
    const sentCount = sendResults.filter(r => r.status === 'success').length;
    const failedCount = sendResults.filter(r => r.status === 'failed').length;
    const progressPercent = sendResults.length > 0
        ? Math.round(((sentCount + failedCount) / sendResults.length) * 100)
        : 0;

    // Estimated time
    const estimatedSeconds = leads.length * (SEND_DELAY_MS / 1000);
    const remainingSeconds = Math.max(0, (leads.length - currentIndex - 1) * (SEND_DELAY_MS / 1000));

    // Leads with valid emails
    const validLeads = leads.filter(l => l.decision_maker?.email || l.email);
    const invalidCount = leads.length - validLeads.length;

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                {/* Backdrop */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={!isSending ? onClose : undefined}
                    className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                />

                {/* Modal */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="relative bg-white rounded-3xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col"
                >
                    {/* Header */}
                    <div className="p-6 border-b border-neutral-100 bg-neutral-900 text-white">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center">
                                    <Rocket className="w-5 h-5" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-black tracking-tight">
                                        {showResults ? 'Mission In Progress' : 'Bulk Outreach'}
                                    </h2>
                                    <p className="text-xs text-white/50 font-medium">
                                        Send personalized emails to {leads.length} selected leads
                                    </p>
                                </div>
                            </div>
                            {!isSending && (
                                <button
                                    onClick={onClose}
                                    className="p-2 text-white/50 hover:text-white hover:bg-white/10 rounded-xl transition-all"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Content */}
                    <div className="flex-1 overflow-y-auto p-6">
                        {!showResults ? (
                            <>
                                {/* Variable Tags */}
                                <div className="mb-6">
                                    <label className="text-[10px] font-black text-neutral-400 uppercase tracking-widest mb-2 block">
                                        Variable Tags (Click to insert)
                                    </label>
                                    <div className="flex flex-wrap gap-2">
                                        {VARIABLE_TAGS.map((tag) => (
                                            <button
                                                key={tag.key}
                                                onClick={() => handleInsertVariable(tag.key)}
                                                className="px-3 py-1.5 bg-neutral-100 hover:bg-neutral-200 rounded-full text-xs font-bold text-neutral-700 transition-colors flex items-center gap-1.5"
                                                title={tag.description}
                                            >
                                                {tag.icon && <tag.icon className="w-3 h-3 text-amber-500" />}
                                                {tag.label}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Subject Field */}
                                <div className="mb-4">
                                    <label className="text-[10px] font-black text-neutral-400 uppercase tracking-widest mb-1 block">
                                        Subject
                                    </label>
                                    <input
                                        ref={subjectRef}
                                        type="text"
                                        value={subject}
                                        onChange={(e) => setSubject(e.target.value)}
                                        onFocus={() => lastFocusedRef.current = 'subject'}
                                        className="w-full px-4 py-3 bg-neutral-50 border border-neutral-200 rounded-xl text-sm font-bold focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                                        placeholder="Email subject line..."
                                    />
                                </div>

                                {/* Body Field */}
                                <div className="mb-6">
                                    <label className="text-[10px] font-black text-neutral-400 uppercase tracking-widest mb-1 block">
                                        Message
                                    </label>
                                    <textarea
                                        ref={bodyRef}
                                        value={body}
                                        onChange={(e) => setBody(e.target.value)}
                                        onFocus={() => lastFocusedRef.current = 'body'}
                                        rows={10}
                                        className="w-full px-4 py-3 bg-neutral-50 border border-neutral-200 rounded-xl text-sm font-mono leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                                        placeholder="Write your email template..."
                                    />
                                </div>

                                {/* Warning for invalid leads */}
                                {invalidCount > 0 && (
                                    <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-2 text-sm">
                                        <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
                                        <span className="text-amber-700">
                                            {invalidCount} lead{invalidCount > 1 ? 's' : ''} without email will be skipped
                                        </span>
                                    </div>
                                )}

                                {/* Safety Counter */}
                                <div className="p-4 bg-neutral-50 rounded-xl space-y-2">
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-neutral-500">Emails to send:</span>
                                        <span className="font-black text-neutral-900">{validLeads.length}</span>
                                    </div>
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-neutral-500">Gmail Daily Safety Limit:</span>
                                        <span className="font-black text-neutral-900">{DAILY_LIMIT}</span>
                                    </div>
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-neutral-500 flex items-center gap-1">
                                            <Clock className="w-3.5 h-3.5" /> Est. Time:
                                        </span>
                                        <span className="font-black text-neutral-900">~{Math.ceil(estimatedSeconds / 60)} min</span>
                                    </div>
                                </div>
                            </>
                        ) : (
                            <>
                                {/* Progress Pipeline */}
                                <div className="space-y-2 mb-6 max-h-[300px] overflow-y-auto">
                                    {sendResults.map((result, index) => (
                                        <div
                                            key={result.leadId}
                                            className={`flex items-center gap-3 p-3 rounded-xl transition-all ${
                                                result.status === 'sending'
                                                    ? 'bg-blue-50 border border-blue-200'
                                                    : result.status === 'success'
                                                        ? 'bg-emerald-50 border border-emerald-200'
                                                        : result.status === 'failed'
                                                            ? 'bg-red-50 border border-red-200'
                                                            : 'bg-neutral-50 border border-neutral-100'
                                            }`}
                                        >
                                            {/* Status Icon */}
                                            <div className="flex-shrink-0">
                                                {result.status === 'pending' && (
                                                    <div className="w-5 h-5 rounded-full border-2 border-neutral-300" />
                                                )}
                                                {result.status === 'sending' && (
                                                    <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                                                )}
                                                {result.status === 'success' && (
                                                    <CheckCircle className="w-5 h-5 text-emerald-500" />
                                                )}
                                                {result.status === 'failed' && (
                                                    <AlertCircle className="w-5 h-5 text-red-500" />
                                                )}
                                            </div>

                                            {/* Lead Name */}
                                            <div className="flex-1 min-w-0">
                                                <span className={`text-sm font-bold truncate block ${
                                                    result.status === 'success'
                                                        ? 'text-emerald-700'
                                                        : result.status === 'failed'
                                                            ? 'text-red-700'
                                                            : result.status === 'sending'
                                                                ? 'text-blue-700'
                                                                : 'text-neutral-500'
                                                }`}>
                                                    {result.leadName}
                                                </span>
                                                {result.status === 'sending' && (
                                                    <span className="text-xs text-blue-500">
                                                        Personalizing and sending...
                                                    </span>
                                                )}
                                                {result.status === 'failed' && result.error && (
                                                    <span className="text-xs text-red-500">
                                                        {result.error}
                                                    </span>
                                                )}
                                            </div>

                                            {/* Status Badge */}
                                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                                                result.status === 'success'
                                                    ? 'bg-emerald-100 text-emerald-700'
                                                    : result.status === 'failed'
                                                        ? 'bg-red-100 text-red-700'
                                                        : result.status === 'sending'
                                                            ? 'bg-blue-100 text-blue-700'
                                                            : 'bg-neutral-200 text-neutral-500'
                                            }`}>
                                                {result.status === 'sending' ? 'Sending' : result.status}
                                            </span>
                                        </div>
                                    ))}
                                </div>

                                {/* Progress Bar */}
                                <div className="p-4 bg-neutral-50 rounded-xl space-y-3">
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-neutral-500">Progress:</span>
                                        <span className="font-black text-neutral-900">
                                            {sentCount + failedCount}/{sendResults.length} sent
                                        </span>
                                    </div>

                                    {/* Progress Bar Visual */}
                                    <div className="h-3 bg-neutral-200 rounded-full overflow-hidden">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            animate={{ width: `${progressPercent}%` }}
                                            className={`h-full ${failedCount > 0 ? 'bg-gradient-to-r from-emerald-500 to-amber-500' : 'bg-emerald-500'}`}
                                            transition={{ duration: 0.3 }}
                                        />
                                    </div>

                                    {isSending && (
                                        <div className="flex items-center justify-between text-sm">
                                            <span className="text-neutral-500 flex items-center gap-1">
                                                <Clock className="w-3.5 h-3.5" /> Estimated:
                                            </span>
                                            <span className="font-bold text-neutral-700">
                                                ~{Math.ceil(remainingSeconds)} seconds remaining
                                            </span>
                                        </div>
                                    )}

                                    {/* Final Stats */}
                                    {!isSending && sendResults.length > 0 && (
                                        <div className="flex items-center justify-center gap-6 pt-2 border-t border-neutral-200">
                                            <div className="text-center">
                                                <div className="text-2xl font-black text-emerald-600">{sentCount}</div>
                                                <div className="text-[10px] text-neutral-500 uppercase tracking-wider">Sent</div>
                                            </div>
                                            {failedCount > 0 && (
                                                <div className="text-center">
                                                    <div className="text-2xl font-black text-red-500">{failedCount}</div>
                                                    <div className="text-[10px] text-neutral-500 uppercase tracking-wider">Failed</div>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </>
                        )}
                    </div>

                    {/* Footer */}
                    <div className="p-6 border-t border-neutral-100 bg-white">
                        {!showResults ? (
                            <button
                                onClick={handleStartMission}
                                disabled={validLeads.length === 0 || !subject.trim() || !body.trim()}
                                className="w-full flex items-center justify-center gap-3 px-6 py-4 bg-neutral-900 text-white rounded-2xl font-black text-sm hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-neutral-900/20"
                            >
                                <Rocket className="w-5 h-5" />
                                <span>START MISSION</span>
                            </button>
                        ) : (
                            <button
                                onClick={onClose}
                                disabled={isSending}
                                className="w-full flex items-center justify-center gap-3 px-6 py-4 bg-neutral-900 text-white rounded-2xl font-black text-sm hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-neutral-900/20"
                            >
                                {isSending ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        <span>Mission in Progress...</span>
                                    </>
                                ) : (
                                    <span>Done</span>
                                )}
                            </button>
                        )}
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
}
