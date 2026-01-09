
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface HuntRequest {
    niche: string;
    location: string;
    limit: number;
    user_id?: string;
}

export interface HuntResponse {
    hunt_id: string;
    message: string;
}

export interface HuntStatus {
    hunt_id: string;
    status: string;
    progress_percent: number;
    stage_message: string;
    leads_found: number;
    owners_found: number;
    emails_found: number;
    started_at: string;
    completed_at?: string;
    error?: string;
}

export const api = {
    async startHunt(data: HuntRequest): Promise<HuntResponse> {
        const response = await fetch(`${API_BASE_URL}/api/hunt`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to start hunt');
        }

        return response.json();
    },

    async getHuntStatus(huntId: string): Promise<HuntStatus> {
        const response = await fetch(`${API_BASE_URL}/api/hunt/${huntId}/status`);
        if (!response.ok) {
            throw new Error('Failed to fetch hunt status');
        }
        return response.json();
    },

    async getLeads(huntId?: string) {
        const url = huntId
            ? `${API_BASE_URL}/api/leads?hunt_id=${huntId}`
            : `${API_BASE_URL}/api/leads`;
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('Failed to fetch leads');
        }
        return response.json();
    },

    getLogSource(huntId: string): EventSource {
        return new EventSource(`${API_BASE_URL}/api/hunt/${huntId}/logs`);
    }
};
