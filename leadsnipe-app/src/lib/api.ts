import { CreateHuntRequest, HuntDetails, Hunt, Lead } from './types';

const API_BASE_URL = 'http://127.0.0.1:8000';

// Helper for type-safe fetch
async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, options);
    if (!res.ok) {
        let errorMessage = `API Error: ${res.status} ${res.statusText}`;
        try {
            const errorBody = await res.json();
            if (errorBody.detail) errorMessage += ` - ${errorBody.detail}`;
        } catch { }
        throw new Error(errorMessage);
    }
    return res.json();
}

// Backend interfaces
interface BackendHunt {
    hunt_id: string;
    niche: string;
    location: string;
    limit?: number;
    limit_count?: number;
    status: 'queued' | 'scraping' | 'finding_owners' | 'getting_emails' | 'generating_outreach' | 'completed' | 'failed';
    started_at: string;
    completed_at?: string;
    leads_found: number;
    owners_found: number;
    emails_found: number;
    stage_message: string;
    progress_percent: number;
}

interface BackendLead {
    id: string;
    place_id?: string;
    name: string;
    address?: string;
    phone?: string;
    website?: string;
    email?: string;
    rating?: number;
    user_ratings_total?: number;
    owner_name?: string;
    linkedin_url?: string;
    email_verified?: boolean;
    // Insight fields
    website_content?: {
        raw_text: string;
        pages_scraped: string[];
        word_count: number;
        scraped_at?: string;
    };
    quick_insights?: string[];
    // Email fields
    email_draft?: {
        subject: string;
        body: string;
        gmail_draft_id?: string;
    };
    email_sent?: boolean;
    email_sent_at?: string;
}

export const api = {
    // Start a new hunt
    createHunt: async (data: CreateHuntRequest): Promise<string> => {
        const res = await fetchJson<{ hunt_id: string; message: string }>('/api/hunt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                niche: data.industry,
                location: data.location,
                limit: data.target,
            }),
        });
        return res.hunt_id;
    },

    // Get list of all hunts
    getHunts: async (): Promise<Hunt[]> => {
        const res = await fetchJson<{ hunts: BackendHunt[]; total: number }>('/api/hunts');
        return res.hunts.map(h => ({
            hunt_id: h.hunt_id,
            industry: h.niche,
            location: h.location,
            target: h.limit_count || h.limit || 0,
            status: h.status === 'queued' ? 'pending' : h.status === 'failed' ? 'failed' : h.status === 'completed' ? 'completed' : 'running',
            created_at: h.started_at,
            completed_at: h.completed_at,
            total_leads: h.leads_found,
        }));
    },

    // Get hunt details (status + leads)
    getHuntDetails: async (huntId: string): Promise<HuntDetails> => {
        // Parallel fetch for status and leads
        const [status, leadsRes] = await Promise.all([
            fetchJson<BackendHunt>(`/api/hunt/${huntId}/status`),
            fetchJson<{ leads: BackendLead[]; total: number }>(`/api/leads?hunt_id=${huntId}`)
        ]);

        // Map leads to frontend structure
        const mappedLeads: Lead[] = leadsRes.leads.map((l) => ({
            id: l.id,
            name: l.name,
            address: l.address || '',
            phone: l.phone || '',
            website: l.website || '',
            email: l.email || '',
            rating: l.rating || 0,
            user_ratings_total: l.user_ratings_total || 0,
            decision_maker: l.owner_name ? {
                full_name: l.owner_name,
                email: l.email || '',
                job_title: 'Owner',
                linkedin_url: l.linkedin_url || null,
                status: l.email_verified ? 'valid' : 'pending'
            } : null,
            // Insight fields
            website_content: l.website_content,
            quick_insights: l.quick_insights,
            // Email fields
            email_draft: l.email_draft,
            email_sent: l.email_sent,
            email_sent_at: l.email_sent_at
        }));

        // Derive hunt status for frontend
        let frontendStatus: 'pending' | 'running' | 'completed' | 'failed' = 'running';
        if (status.status === 'queued') frontendStatus = 'pending';
        else if (status.status === 'completed') frontendStatus = 'completed';
        else if (status.status === 'failed') frontendStatus = 'failed';

        // Map backend status to frontend stage number
        const stageMap: Record<string, 1 | 2 | 3> = {
            'queued': 1, 'scraping': 1,
            'finding_owners': 2,
            'getting_emails': 3, 'generating_outreach': 3,
            'completed': 3, 'failed': 1
        };

        return {
            hunt_id: status.hunt_id,
            industry: status.niche || 'Unknown',
            location: status.location || 'Unknown',
            target: status.limit || 0,
            status: frontendStatus,
            created_at: status.started_at,
            completed_at: status.completed_at,
            leads: mappedLeads,
            stats: {
                total_leads: status.leads_found,
                ceos_found: status.owners_found,
                linkedin_found: status.emails_found,
            },
            progress: {
                stage: stageMap[status.status] || 1,
                stage_name: status.stage_message,
                percentage: status.progress_percent,
                processed: status.leads_found,
                total: status.limit || 0,
                elapsed_time: 0,
                estimated_total: 0
            }
        };
    },

    // Gmail endpoints
    getGmailStatus: async (): Promise<{ gmail_connected: boolean; gmail_email?: string }> => {
        return fetchJson<{ gmail_connected: boolean; gmail_email?: string; status: string }>('/api/gmail/status');
    },

    connectGmail: async (): Promise<{ auth_url: string }> => {
        return fetchJson<{ auth_url: string }>('/api/gmail/connect');
    },

    // ========== Insight Engine APIs ==========

    // Get cached insights for a lead
    getLeadInsights: async (leadId: string): Promise<{
        quick_insights: string[];
        website_content: { raw_text: string; pages_scraped: string[]; word_count: number } | null
    }> => {
        return fetchJson(`/api/lead/${leadId}/insights`);
    },

    // Generate insights for a lead (if not cached)
    generateInsights: async (leadId: string): Promise<{
        quick_insights: string[];
        website_content: { raw_text: string; pages_scraped: string[]; word_count: number }
    }> => {
        return fetchJson(`/api/lead/${leadId}/insights/generate`, { method: 'POST' });
    },

    // Ask any question about a lead's website
    askInsightQuestion: async (leadId: string, question: string): Promise<{ answer: string }> => {
        return fetchJson(`/api/lead/${leadId}/insights/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
    },

    // ========== Email Send APIs ==========

    // Send a single email
    sendEmail: async (to: string, subject: string, body: string): Promise<{
        success: boolean;
        message_id?: string;
        error?: string
    }> => {
        return fetchJson('/api/email/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ to_email: to, subject, body })
        });
    },

    // Send emails to multiple leads
    sendBulkEmails: async (emails: Array<{ to_email: string; subject: string; body: string }>): Promise<{
        total: number;
        sent: number;
        failed: number;
        results: Array<{ to: string; success: boolean; error?: string }>
    }> => {
        return fetchJson('/api/email/send-bulk', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ emails })
        });
    }
};
