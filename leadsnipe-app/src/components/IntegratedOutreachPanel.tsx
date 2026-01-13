'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
    X,
    Sparkles,
    MessageSquare,
    Send,
    Loader2,
    Mail,
    ExternalLink,
    CheckCircle,
    AlertCircle,
    Building2,
    ArrowDown,
    User,
} from 'lucide-react';
import type { Lead } from '@/lib/types';
import { api } from '@/lib/api';

interface IntegratedOutreachPanelProps {
    lead: Lead | null;
    isOpen: boolean;
    onClose: () => void;
    onEmailSent?: (lead: Lead) => void;
}

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    id: string;
}

export function IntegratedOutreachPanel({ lead, isOpen, onClose, onEmailSent }: IntegratedOutreachPanelProps) {
    // Intel State
    const [insights, setInsights] = useState<string[]>([]);
    const [loadingInsights, setLoadingInsights] = useState(false);
    const [question, setQuestion] = useState('');
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [askingQuestion, setAskingQuestion] = useState(false);

    // Email State
    const [emailTo, setEmailTo] = useState('');
    const [emailSubject, setEmailSubject] = useState('');
    const [emailBody, setEmailBody] = useState('');
    const [sendingEmail, setSendingEmail] = useState(false);
    const [emailSent, setEmailSent] = useState(false);
    const [sendError, setSendError] = useState<string | null>(null);

    const chatEndRef = useRef<HTMLDivElement>(null);
    const emailBodyRef = useRef<HTMLTextAreaElement>(null);

    // Initialize when lead changes
    useEffect(() => {
        if (lead && isOpen) {
            loadInsights();
            initializeEmail();
            setChatMessages([]);
            setEmailSent(false);
            setSendError(null);
        }
    }, [lead?.id, isOpen]);

    // Scroll chat to bottom
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [chatMessages]);

    const loadInsights = async () => {
        if (!lead) return;

        // Check cached insights first
        if (lead.quick_insights && lead.quick_insights.length > 0) {
            setInsights(lead.quick_insights);
            return;
        }

        // Auto-generate if missing
        setLoadingInsights(true);
        try {
            const result = await api.generateInsights(lead.id);
            setInsights(result.quick_insights || []);
        } catch (error) {
            console.error('Failed to load insights:', error);
            setInsights(['Unable to generate insights. Check website availability.']);
        } finally {
            setLoadingInsights(false);
        }
    };

    const initializeEmail = () => {
        if (!lead) return;

        // Set recipient
        const recipientEmail = lead.decision_maker?.email || lead.email || '';
        setEmailTo(recipientEmail);

        // Pre-fill from draft if available
        if (lead.email_draft) {
            setEmailSubject(lead.email_draft.subject || '');
            setEmailBody(lead.email_draft.body || '');
        } else {
            // Default template
            const ownerName = lead.decision_maker?.full_name?.split(' ')[0] || 'there';
            setEmailSubject(`Quick question about ${lead.name}`);
            setEmailBody(`Hi ${ownerName},

I came across ${lead.name} and was impressed by what you've built.

[Your personalized message here]

Would love to connect and share some ideas that might be helpful.

Best regards`);
        }
    };

    const handleAskQuestion = async () => {
        if (!question.trim() || !lead || askingQuestion) return;

        const userMessage = question.trim();
        const messageId = Date.now().toString();
        setQuestion('');
        setChatMessages(prev => [...prev, { role: 'user', content: userMessage, id: `user-${messageId}` }]);
        setAskingQuestion(true);

        try {
            const result = await api.askInsightQuestion(lead.id, userMessage);
            setChatMessages(prev => [...prev, {
                role: 'assistant',
                content: result.answer,
                id: `assistant-${messageId}`
            }]);
        } catch (error) {
            console.error('Failed to ask question:', error);
            setChatMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, I couldn\'t process that question. Please try again.',
                id: `error-${messageId}`
            }]);
        } finally {
            setAskingQuestion(false);
        }
    };

    const handleInsertToEmail = (text: string) => {
        // Insert text at cursor position or append
        if (emailBodyRef.current) {
            const textarea = emailBodyRef.current;
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            const newBody = emailBody.substring(0, start) + text + emailBody.substring(end);
            setEmailBody(newBody);

            // Focus and set cursor after inserted text
            setTimeout(() => {
                textarea.focus();
                textarea.setSelectionRange(start + text.length, start + text.length);
            }, 0);
        } else {
            setEmailBody(prev => prev + '\n\n' + text);
        }
    };

    const handleSendEmail = async () => {
        if (!lead || !emailTo || sendingEmail) return;

        setSendingEmail(true);
        setSendError(null);

        try {
            const result = await api.sendEmail(emailTo, emailSubject, emailBody);

            if (result.success) {
                setEmailSent(true);
                onEmailSent?.(lead);
            } else {
                setSendError(result.error || 'Failed to send email');
            }
        } catch (error) {
            console.error('Failed to send email:', error);
            setSendError('Failed to send email. Please try again.');
        } finally {
            setSendingEmail(false);
        }
    };

    const suggestedQuestions = [
        'What can I sell them?',
        'What are their pain points?',
        'How can I help them?',
    ];

    if (!lead) return null;

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40"
                    />

                    {/* Panel */}
                    <motion.div
                        initial={{ x: '100%' }}
                        animate={{ x: 0 }}
                        exit={{ x: '100%' }}
                        transition={{ type: 'spring', damping: 30, stiffness: 300 }}
                        className="fixed right-0 top-0 h-full w-full max-w-2xl bg-white shadow-2xl z-50 flex flex-col"
                    >
                        {/* Header */}
                        <div className="p-6 border-b border-neutral-100 bg-neutral-900 text-white">
                            <div className="flex items-start justify-between">
                                <div className="flex items-start gap-4">
                                    <div className="w-12 h-12 bg-white/10 rounded-2xl flex items-center justify-center">
                                        <Building2 className="w-6 h-6 text-white" />
                                    </div>
                                    <div>
                                        <h2 className="text-lg font-black tracking-tight">
                                            {lead.name}
                                        </h2>
                                        <p className="text-xs text-white/50 font-medium mt-0.5">
                                            Outreach Command Center
                                        </p>
                                    </div>
                                </div>
                                <button
                                    onClick={onClose}
                                    className="p-2 text-white/50 hover:text-white hover:bg-white/10 rounded-xl transition-all"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            {/* Recipient Badge */}
                            <div className="mt-4 flex items-center gap-2">
                                <User className="w-4 h-4 text-white/40" />
                                <span className="text-sm font-medium text-white/80">
                                    {lead.decision_maker?.full_name || 'Decision Maker'}
                                </span>
                                {lead.decision_maker?.job_title && (
                                    <span className="text-xs text-white/40">
                                        {lead.decision_maker.job_title}
                                    </span>
                                )}
                            </div>
                        </div>

                        {/* Split Content */}
                        <div className="flex-1 overflow-hidden flex flex-col">
                            {/* INTEL SECTION (Top) */}
                            <div className="flex-1 overflow-y-auto border-b border-neutral-200">
                                <div className="p-6">
                                    {/* Section Header */}
                                    <div className="flex items-center gap-2 mb-4">
                                        <Sparkles className="w-4 h-4 text-amber-500" />
                                        <h3 className="text-xs font-black text-neutral-900 uppercase tracking-widest">
                                            Intel Context
                                        </h3>
                                    </div>

                                    {/* Quick Insights */}
                                    {loadingInsights ? (
                                        <div className="space-y-2 mb-6">
                                            {[1, 2, 3].map(i => (
                                                <div key={i} className="h-4 bg-neutral-100 rounded animate-pulse" />
                                            ))}
                                        </div>
                                    ) : (
                                        <ul className="space-y-2 mb-6">
                                            {insights.map((insight, i) => (
                                                <li key={i} className="flex items-start gap-2 group">
                                                    <div className="w-1.5 h-1.5 bg-neutral-400 rounded-full mt-1.5 flex-shrink-0" />
                                                    <span className="text-sm text-neutral-600 leading-relaxed flex-1">
                                                        {insight}
                                                    </span>
                                                    <button
                                                        onClick={() => handleInsertToEmail(insight)}
                                                        className="opacity-0 group-hover:opacity-100 p-1 text-neutral-400 hover:text-neutral-900 hover:bg-neutral-100 rounded transition-all"
                                                        title="Insert into email"
                                                    >
                                                        <ArrowDown className="w-3.5 h-3.5" />
                                                    </button>
                                                </li>
                                            ))}
                                        </ul>
                                    )}

                                    {/* AI Chat */}
                                    <div className="border-t border-neutral-100 pt-4">
                                        <div className="flex items-center gap-2 mb-3">
                                            <MessageSquare className="w-4 h-4 text-blue-500" />
                                            <h4 className="text-xs font-black text-neutral-900 uppercase tracking-widest">
                                                Ask AI
                                            </h4>
                                        </div>

                                        {/* Suggested Questions */}
                                        {chatMessages.length === 0 && (
                                            <div className="flex flex-wrap gap-2 mb-3">
                                                {suggestedQuestions.map((q, i) => (
                                                    <button
                                                        key={i}
                                                        onClick={() => setQuestion(q)}
                                                        className="px-3 py-1.5 text-xs font-medium text-neutral-600 bg-neutral-100 rounded-full hover:bg-neutral-200 transition-colors"
                                                    >
                                                        {q}
                                                    </button>
                                                ))}
                                            </div>
                                        )}

                                        {/* Chat Messages */}
                                        <div className="space-y-3 max-h-32 overflow-y-auto mb-3">
                                            {chatMessages.map((msg) => (
                                                <div key={msg.id} className="flex items-start gap-2">
                                                    {msg.role === 'assistant' ? (
                                                        <div className="flex-1 bg-neutral-100 p-3 rounded-xl text-sm text-neutral-700 group">
                                                            <div className="flex items-start justify-between gap-2">
                                                                <span>{msg.content}</span>
                                                                <button
                                                                    onClick={() => handleInsertToEmail(msg.content)}
                                                                    className="opacity-0 group-hover:opacity-100 flex-shrink-0 px-2 py-1 text-xs font-bold text-neutral-500 hover:text-neutral-900 hover:bg-neutral-200 rounded transition-all flex items-center gap-1"
                                                                >
                                                                    <ArrowDown className="w-3 h-3" />
                                                                    Insert
                                                                </button>
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        <div className="ml-auto bg-neutral-900 text-white px-3 py-2 rounded-xl text-sm">
                                                            {msg.content}
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                            {askingQuestion && (
                                                <div className="bg-neutral-100 p-3 rounded-xl">
                                                    <Loader2 className="w-4 h-4 animate-spin text-neutral-500" />
                                                </div>
                                            )}
                                            <div ref={chatEndRef} />
                                        </div>

                                        {/* Input */}
                                        <div className="flex gap-2">
                                            <input
                                                type="text"
                                                value={question}
                                                onChange={(e) => setQuestion(e.target.value)}
                                                onKeyDown={(e) => e.key === 'Enter' && handleAskQuestion()}
                                                placeholder="Ask about this business..."
                                                className="flex-1 px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-lg text-sm placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                                            />
                                            <button
                                                onClick={handleAskQuestion}
                                                disabled={!question.trim() || askingQuestion}
                                                className="px-3 py-2 bg-neutral-900 text-white rounded-lg hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                                            >
                                                <Send className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* EMAIL SECTION (Bottom) */}
                            <div className="flex-1 overflow-y-auto bg-neutral-50">
                                <div className="p-6">
                                    {/* Section Header */}
                                    <div className="flex items-center gap-2 mb-4">
                                        <Mail className="w-4 h-4 text-neutral-900" />
                                        <h3 className="text-xs font-black text-neutral-900 uppercase tracking-widest">
                                            Compose Email
                                        </h3>
                                    </div>

                                    {emailSent ? (
                                        <div className="flex flex-col items-center justify-center py-12">
                                            <div className="w-16 h-16 bg-emerald-100 rounded-2xl flex items-center justify-center mb-4">
                                                <CheckCircle className="w-8 h-8 text-emerald-600" />
                                            </div>
                                            <h4 className="text-lg font-black text-neutral-900 mb-2">Email Sent!</h4>
                                            <p className="text-sm text-neutral-500 text-center">
                                                Your outreach to {lead.decision_maker?.full_name || lead.name} has been delivered.
                                            </p>
                                            <button
                                                onClick={onClose}
                                                className="mt-6 px-6 py-2 bg-neutral-900 text-white rounded-xl font-bold hover:bg-neutral-800 transition-all"
                                            >
                                                Done
                                            </button>
                                        </div>
                                    ) : (
                                        <>
                                            {/* To Field */}
                                            <div className="mb-4">
                                                <label className="text-[10px] font-black text-neutral-400 uppercase tracking-widest mb-1 block">
                                                    To
                                                </label>
                                                <input
                                                    type="email"
                                                    value={emailTo}
                                                    onChange={(e) => setEmailTo(e.target.value)}
                                                    className="w-full px-4 py-3 bg-white border border-neutral-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                                                />
                                            </div>

                                            {/* Subject Field */}
                                            <div className="mb-4">
                                                <label className="text-[10px] font-black text-neutral-400 uppercase tracking-widest mb-1 block">
                                                    Subject
                                                </label>
                                                <input
                                                    type="text"
                                                    value={emailSubject}
                                                    onChange={(e) => setEmailSubject(e.target.value)}
                                                    className="w-full px-4 py-3 bg-white border border-neutral-200 rounded-xl text-sm font-bold focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                                                />
                                            </div>

                                            {/* Body Field */}
                                            <div className="mb-4">
                                                <label className="text-[10px] font-black text-neutral-400 uppercase tracking-widest mb-1 block">
                                                    Message
                                                </label>
                                                <textarea
                                                    ref={emailBodyRef}
                                                    value={emailBody}
                                                    onChange={(e) => setEmailBody(e.target.value)}
                                                    rows={8}
                                                    className="w-full px-4 py-3 bg-white border border-neutral-200 rounded-xl text-sm font-mono leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                                                />
                                            </div>

                                            {/* Error Message */}
                                            {sendError && (
                                                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2 text-sm text-red-700">
                                                    <AlertCircle className="w-4 h-4" />
                                                    {sendError}
                                                </div>
                                            )}
                                        </>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Footer - Send Button */}
                        {!emailSent && (
                            <div className="p-6 border-t border-neutral-200 bg-white">
                                <button
                                    onClick={handleSendEmail}
                                    disabled={sendingEmail || !emailTo || !emailSubject || !emailBody}
                                    className="w-full flex items-center justify-center gap-3 px-6 py-4 bg-neutral-900 text-white rounded-2xl font-black text-sm hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-neutral-900/20"
                                >
                                    {sendingEmail ? (
                                        <>
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                            <span>Sending...</span>
                                        </>
                                    ) : (
                                        <>
                                            <Mail className="w-5 h-5" />
                                            <span>SEND VIA GMAIL</span>
                                        </>
                                    )}
                                </button>
                            </div>
                        )}
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
