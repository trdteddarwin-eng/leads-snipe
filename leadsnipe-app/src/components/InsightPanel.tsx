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
    Building2
} from 'lucide-react';
import type { Lead } from '@/lib/types';
import { api } from '@/lib/api';

interface InsightPanelProps {
    lead: Lead | null;
    isOpen: boolean;
    onClose: () => void;
    onSendEmail?: (lead: Lead) => void;
}

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
}

export function InsightPanel({ lead, isOpen, onClose, onSendEmail }: InsightPanelProps) {
    const [insights, setInsights] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [question, setQuestion] = useState('');
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [askingQuestion, setAskingQuestion] = useState(false);
    const [sendingEmail, setSendingEmail] = useState(false);
    const [emailSent, setEmailSent] = useState(false);
    const chatEndRef = useRef<HTMLDivElement>(null);

    // Load insights when lead changes
    useEffect(() => {
        if (lead && isOpen) {
            loadInsights();
            setChatMessages([]);
            setEmailSent(false);
        }
    }, [lead?.id, isOpen]);

    // Scroll to bottom on new messages
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [chatMessages]);

    const loadInsights = async () => {
        if (!lead) return;

        // Check if insights are already cached in lead
        if (lead.quick_insights && lead.quick_insights.length > 0) {
            setInsights(lead.quick_insights);
            return;
        }

        setLoading(true);
        try {
            const result = await api.generateInsights(lead.id);
            setInsights(result.quick_insights || []);
        } catch (error) {
            console.error('Failed to load insights:', error);
            setInsights(['Unable to generate insights for this business']);
        } finally {
            setLoading(false);
        }
    };

    const handleAskQuestion = async () => {
        if (!question.trim() || !lead || askingQuestion) return;

        const userMessage = question.trim();
        setQuestion('');
        setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setAskingQuestion(true);

        try {
            const result = await api.askInsightQuestion(lead.id, userMessage);
            setChatMessages(prev => [...prev, { role: 'assistant', content: result.answer }]);
        } catch (error) {
            console.error('Failed to ask question:', error);
            setChatMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, I couldn\'t process that question. Please try again.'
            }]);
        } finally {
            setAskingQuestion(false);
        }
    };

    const handleSendEmail = async () => {
        if (!lead || !lead.email_draft || sendingEmail) return;

        setSendingEmail(true);
        try {
            const email = lead.decision_maker?.email || lead.email;
            if (!email) throw new Error('No email address');

            const result = await api.sendEmail(
                email,
                lead.email_draft.subject,
                lead.email_draft.body
            );

            if (result.success) {
                setEmailSent(true);
                onSendEmail?.(lead);
            }
        } catch (error) {
            console.error('Failed to send email:', error);
        } finally {
            setSendingEmail(false);
        }
    };

    const suggestedQuestions = [
        'What can I sell them?',
        'What are their weaknesses?',
        'How can I help them?',
        'What makes them unique?'
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
                        className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40"
                    />

                    {/* Panel */}
                    <motion.div
                        initial={{ x: '100%' }}
                        animate={{ x: 0 }}
                        exit={{ x: '100%' }}
                        transition={{ type: 'spring', damping: 30, stiffness: 300 }}
                        className="fixed right-0 top-0 h-full w-full max-w-lg bg-white shadow-2xl z-50 flex flex-col"
                    >
                        {/* Header */}
                        <div className="p-6 border-b border-neutral-100">
                            <div className="flex items-start justify-between">
                                <div className="flex items-start gap-4">
                                    <div className="w-12 h-12 bg-neutral-900 rounded-2xl flex items-center justify-center">
                                        <Building2 className="w-6 h-6 text-white" />
                                    </div>
                                    <div>
                                        <h2 className="text-lg font-black text-neutral-900 tracking-tight">
                                            {lead.name}
                                        </h2>
                                        <p className="text-xs text-neutral-400 font-medium mt-0.5">
                                            Business Intelligence
                                        </p>
                                    </div>
                                </div>
                                <button
                                    onClick={onClose}
                                    className="p-2 text-neutral-400 hover:text-neutral-900 hover:bg-neutral-100 rounded-xl transition-all"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            {/* Website link */}
                            {lead.website && (
                                <a
                                    href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="mt-4 flex items-center gap-2 text-xs text-neutral-500 hover:text-neutral-900 transition-colors"
                                >
                                    <ExternalLink className="w-3.5 h-3.5" />
                                    <span className="font-medium truncate">{lead.website}</span>
                                </a>
                            )}
                        </div>

                        {/* Content */}
                        <div className="flex-1 overflow-y-auto">
                            {/* Quick Insights */}
                            <div className="p-6 border-b border-neutral-100">
                                <div className="flex items-center gap-2 mb-4">
                                    <Sparkles className="w-4 h-4 text-amber-500" />
                                    <h3 className="text-xs font-black text-neutral-900 uppercase tracking-widest">
                                        Quick Insights
                                    </h3>
                                </div>

                                {loading ? (
                                    <div className="space-y-3">
                                        {[1, 2, 3, 4, 5].map(i => (
                                            <div key={i} className="h-4 bg-neutral-100 rounded animate-pulse" />
                                        ))}
                                    </div>
                                ) : (
                                    <ul className="space-y-3">
                                        {insights.map((insight, i) => (
                                            <li key={i} className="flex items-start gap-3">
                                                <div className="w-1.5 h-1.5 bg-neutral-900 rounded-full mt-1.5 flex-shrink-0" />
                                                <span className="text-sm text-neutral-600 leading-relaxed">
                                                    {insight}
                                                </span>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </div>

                            {/* Chat Section */}
                            <div className="p-6">
                                <div className="flex items-center gap-2 mb-4">
                                    <MessageSquare className="w-4 h-4 text-blue-500" />
                                    <h3 className="text-xs font-black text-neutral-900 uppercase tracking-widest">
                                        Ask Anything
                                    </h3>
                                </div>

                                {/* Suggested Questions */}
                                {chatMessages.length === 0 && (
                                    <div className="flex flex-wrap gap-2 mb-4">
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
                                <div className="space-y-4 max-h-64 overflow-y-auto mb-4">
                                    {chatMessages.map((msg, i) => (
                                        <div
                                            key={i}
                                            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                        >
                                            <div
                                                className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm ${msg.role === 'user'
                                                        ? 'bg-neutral-900 text-white'
                                                        : 'bg-neutral-100 text-neutral-700'
                                                    }`}
                                            >
                                                {msg.content}
                                            </div>
                                        </div>
                                    ))}
                                    {askingQuestion && (
                                        <div className="flex justify-start">
                                            <div className="bg-neutral-100 px-4 py-3 rounded-2xl">
                                                <Loader2 className="w-4 h-4 animate-spin text-neutral-500" />
                                            </div>
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
                                        className="flex-1 px-4 py-3 bg-neutral-50 border border-neutral-200 rounded-xl text-sm placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                                    />
                                    <button
                                        onClick={handleAskQuestion}
                                        disabled={!question.trim() || askingQuestion}
                                        className="px-4 py-3 bg-neutral-900 text-white rounded-xl hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                                    >
                                        <Send className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Footer - Send Email */}
                        {lead.email_draft && (
                            <div className="p-6 border-t border-neutral-100 bg-neutral-50">
                                {emailSent ? (
                                    <div className="flex items-center justify-center gap-2 py-3 text-emerald-600">
                                        <CheckCircle className="w-5 h-5" />
                                        <span className="text-sm font-bold">Email Sent Successfully!</span>
                                    </div>
                                ) : (
                                    <button
                                        onClick={handleSendEmail}
                                        disabled={sendingEmail}
                                        className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-neutral-900 text-white rounded-2xl font-bold hover:bg-neutral-800 disabled:opacity-50 transition-all shadow-lg shadow-neutral-900/20"
                                    >
                                        {sendingEmail ? (
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                        ) : (
                                            <Mail className="w-5 h-5" />
                                        )}
                                        <span>
                                            {sendingEmail ? 'Sending...' : 'Send Personalized Email'}
                                        </span>
                                    </button>
                                )}

                                {/* Email Preview */}
                                <div className="mt-4 p-4 bg-white rounded-xl border border-neutral-200">
                                    <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest mb-2">
                                        Email Preview
                                    </p>
                                    <p className="text-xs font-bold text-neutral-900 mb-1">
                                        {lead.email_draft.subject}
                                    </p>
                                    <p className="text-xs text-neutral-500 line-clamp-2">
                                        {lead.email_draft.body.substring(0, 100)}...
                                    </p>
                                </div>
                            </div>
                        )}
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
