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
            } : null
        }));

        // Derive hunt status for frontend
        let frontendStatus: 'pending' | 'running' | 'completed' | 'failed' = 'running';
        if (status.status === 'queued') frontendStatus = 'pending';
        else if (status.status === 'completed') frontendStatus = 'completed';
        else if (status.status === 'failed') frontendStatus = 'failed';

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
                stage: 1, // simplified
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
    }
};
