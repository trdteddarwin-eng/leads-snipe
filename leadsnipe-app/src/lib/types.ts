// LeadSnipe Type Definitions

export interface DecisionMaker {
  email: string;
  full_name: string;
  job_title: string;
  linkedin_url: string | null;
  linkedin_source?: string;
  status: 'valid' | 'invalid' | 'pending';
}

export interface WebsiteContent {
  raw_text: string;
  pages_scraped: string[];
  word_count: number;
  scraped_at?: string;
}

export interface EmailDraft {
  subject: string;
  body: string;
  gmail_draft_id?: string;
}

export interface Lead {
  id: string;
  name: string;
  address: string;
  phone: string;
  website: string;
  email: string;
  rating: number;
  user_ratings_total: number;
  decision_maker: DecisionMaker | null;
  // Insight Engine fields
  website_content?: WebsiteContent;
  quick_insights?: string[];
  // Email fields
  email_draft?: EmailDraft;
  email_sent?: boolean;
  email_sent_at?: string;
}

export interface HuntProgress {
  stage: 1 | 2 | 3;
  stage_name: string;
  percentage: number;
  processed: number;
  total: number;
  elapsed_time: number;
  estimated_total: number;
}

export interface HuntStats {
  total_leads: number;
  ceos_found: number;
  linkedin_found: number;
  cost?: number;
}

export interface HuntPerformance {
  total_time: number;
  stage1_time: number;
  stage2_time: number;
  stage3_time: number;
}

export interface Hunt {
  hunt_id: string;
  industry: string;
  location: string;
  target: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  total_leads?: number;
  cost?: number;
}

export interface HuntDetails extends Hunt {
  progress?: HuntProgress;
  stats?: HuntStats;
  performance?: HuntPerformance;
  leads?: Lead[];
  error?: string;
}

export interface ActivityEvent {
  id: string;
  timestamp: string;
  type: 'success' | 'info' | 'warning' | 'error';
  message: string;
}

export interface CreateHuntRequest {
  industry: string;
  location: string;
  target: number;
  category: string;
}

export interface CreateHuntResponse {
  hunt_id: string;
  status: string;
  created_at: string;
}

// Stage definitions
export const HUNT_STAGES = [
  { id: 1, name: 'Google Maps Scraping', description: 'Finding businesses from Google Maps' },
  { id: 2, name: 'Decision Maker Finding', description: 'Finding CEO/owner emails via Anymailfinder' },
  { id: 3, name: 'LinkedIn Discovery', description: 'Finding LinkedIn profiles via DuckDuckGo' },
] as const;

// Industry suggestions
export const INDUSTRY_SUGGESTIONS = [
  'HVAC contractor',
  'Plumber',
  'Electrician',
  'Dentist',
  'Chiropractor',
  'Auto repair shop',
  'Landscaping',
  'Roofing contractor',
  'Real estate agent',
  'Insurance agency',
  'Law firm',
  'Accounting firm',
  'Marketing agency',
  'IT services',
  'Construction company',
];

// Location suggestions
export const LOCATION_SUGGESTIONS = [
  'New Jersey',
  'New York',
  'California',
  'Texas',
  'Florida',
  'Pennsylvania',
  'Phoenix area',
  'Los Angeles area',
  'Chicago area',
  'Houston area',
  'Miami area',
  'Atlanta area',
];

// Decision maker categories
export const DECISION_MAKER_CATEGORIES = [
  { value: 'ceo', label: 'CEO / Owner' },
  { value: 'cfo', label: 'CFO / Finance' },
  { value: 'cto', label: 'CTO / Technical' },
  { value: 'cmo', label: 'CMO / Marketing' },
  { value: 'coo', label: 'COO / Operations' },
  { value: 'hr', label: 'HR Director' },
  { value: 'sales', label: 'Sales Director' },
];
