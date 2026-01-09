// In-memory store for demo purposes
// In production, replace with database (SQLite, PostgreSQL, etc.)

import type { Hunt, HuntDetails, Lead, HuntProgress, ActivityEvent } from './types';
import { v4 as uuidv4 } from 'uuid';

interface HuntStore {
  hunts: Map<string, HuntDetails>;
  progress: Map<string, HuntProgress>;
  events: Map<string, ActivityEvent[]>;
}

const store: HuntStore = {
  hunts: new Map(),
  progress: new Map(),
  events: new Map(),
};

// Generate mock leads
function generateMockLeads(count: number, industry: string): Lead[] {
  const firstNames = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Emily', 'Robert', 'Lisa', 'James', 'Amanda'];
  const lastNames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez'];
  const titles = ['CEO', 'Owner', 'President', 'Founder', 'Managing Director'];
  const cities = ['Newark', 'Jersey City', 'Paterson', 'Elizabeth', 'Edison', 'Woodbridge', 'Lakewood', 'Toms River', 'Hamilton', 'Trenton'];

  return Array.from({ length: count }, (_, i) => {
    const firstName = firstNames[Math.floor(Math.random() * firstNames.length)];
    const lastName = lastNames[Math.floor(Math.random() * lastNames.length)];
    const city = cities[Math.floor(Math.random() * cities.length)];
    const businessName = `${lastName}'s ${industry.split(' ')[0]} Services`;
    const domain = `${lastName.toLowerCase()}${industry.split(' ')[0].toLowerCase()}.com`;
    const hasCeo = Math.random() > 0.3;
    const hasLinkedin = hasCeo && Math.random() > 0.4;

    return {
      id: uuidv4(),
      name: businessName,
      address: `${100 + i * 10} Main St, ${city}, NJ ${Math.floor(7000 + Math.random() * 900)}`,
      phone: `(${Math.floor(200 + Math.random() * 700)}) ${Math.floor(100 + Math.random() * 900)}-${Math.floor(1000 + Math.random() * 9000)}`,
      website: domain,
      email: `info@${domain}`,
      rating: Math.round((3.5 + Math.random() * 1.5) * 10) / 10,
      user_ratings_total: Math.floor(20 + Math.random() * 200),
      decision_maker: hasCeo ? {
        email: `${firstName.toLowerCase()}@${domain}`,
        full_name: `${firstName} ${lastName}`,
        job_title: titles[Math.floor(Math.random() * titles.length)],
        linkedin_url: hasLinkedin ? `https://linkedin.com/in/${firstName.toLowerCase()}${lastName.toLowerCase()}` : null,
        status: 'valid' as const,
      } : null,
    };
  });
}

// Create a new hunt
export function createHunt(data: {
  industry: string;
  location: string;
  target: number;
  category: string;
}): HuntDetails {
  const huntId = `hunt_${Date.now()}_${uuidv4().slice(0, 8)}`;
  const now = new Date().toISOString();

  const hunt: HuntDetails = {
    hunt_id: huntId,
    industry: data.industry,
    location: data.location,
    target: data.target,
    status: 'running',
    created_at: now,
  };

  store.hunts.set(huntId, hunt);
  store.progress.set(huntId, {
    stage: 1,
    stage_name: 'Google Maps Scraping',
    percentage: 0,
    processed: 0,
    total: data.target,
    elapsed_time: 0,
    estimated_total: data.target * 5,
  });
  store.events.set(huntId, []);

  // Simulate hunt completion after delay
  simulateHunt(huntId, data);

  return hunt;
}

// Simulate hunt progress
async function simulateHunt(huntId: string, data: { industry: string; location: string; target: number }) {
  const stages = [
    { name: 'Google Maps Scraping', duration: 3000 },
    { name: 'Decision Maker Finding', duration: 5000 },
    { name: 'LinkedIn Discovery', duration: 2000 },
  ];

  let elapsed = 0;

  for (let stageIndex = 0; stageIndex < stages.length; stageIndex++) {
    const stage = stages[stageIndex];
    const stageNum = (stageIndex + 1) as 1 | 2 | 3;

    // Update progress for this stage
    for (let progress = 0; progress <= 100; progress += 20) {
      await new Promise(resolve => setTimeout(resolve, stage.duration / 5));
      elapsed += stage.duration / 5 / 1000;

      const overallProgress = Math.round(((stageIndex * 100) + progress) / 3);

      store.progress.set(huntId, {
        stage: stageNum,
        stage_name: stage.name,
        percentage: overallProgress,
        processed: Math.round((overallProgress / 100) * data.target),
        total: data.target,
        elapsed_time: elapsed,
        estimated_total: data.target * 5,
      });

      // Add random events
      if (Math.random() > 0.6) {
        const events = store.events.get(huntId) || [];
        events.push({
          id: uuidv4(),
          timestamp: new Date().toISOString(),
          type: Math.random() > 0.3 ? 'success' : 'info',
          message: stageNum === 1
            ? `Found business: ${data.industry} #${Math.floor(Math.random() * 100)}`
            : stageNum === 2
              ? `Found CEO email for lead ${Math.floor(Math.random() * data.target)}`
              : `Found LinkedIn profile`,
        });
        store.events.set(huntId, events);
      }
    }
  }

  // Complete the hunt
  const leads = generateMockLeads(data.target, data.industry);
  const hunt = store.hunts.get(huntId);

  if (hunt) {
    const ceoCount = leads.filter(l => l.decision_maker?.status === 'valid').length;
    const linkedinCount = leads.filter(l => l.decision_maker?.linkedin_url).length;

    hunt.status = 'completed';
    hunt.completed_at = new Date().toISOString();
    hunt.leads = leads;
    hunt.total_leads = leads.length;
    hunt.stats = {
      total_leads: leads.length,
      ceos_found: ceoCount,
      linkedin_found: linkedinCount,
      cost: ceoCount * 0.04,
    };
    hunt.performance = {
      total_time: elapsed,
      stage1_time: 3,
      stage2_time: 5,
      stage3_time: 2,
    };

    store.hunts.set(huntId, hunt);
  }
}

// Get all hunts
export function getAllHunts(): Hunt[] {
  return Array.from(store.hunts.values())
    .map(h => ({
      hunt_id: h.hunt_id,
      industry: h.industry,
      location: h.location,
      target: h.target,
      status: h.status,
      created_at: h.created_at,
      completed_at: h.completed_at,
      total_leads: h.total_leads,
      cost: h.stats?.cost,
    }))
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
}

// Get hunt by ID
export function getHunt(huntId: string): HuntDetails | null {
  return store.hunts.get(huntId) || null;
}

// Get hunt progress
export function getHuntProgress(huntId: string): HuntProgress | null {
  return store.progress.get(huntId) || null;
}

// Get hunt events
export function getHuntEvents(huntId: string): ActivityEvent[] {
  return store.events.get(huntId) || [];
}

// Delete hunt
export function deleteHunt(huntId: string): boolean {
  store.hunts.delete(huntId);
  store.progress.delete(huntId);
  store.events.delete(huntId);
  return true;
}

// Add seed data for demo
export function seedDemoData() {
  if (store.hunts.size > 0) return;

  const demoHunts = [
    { industry: 'HVAC contractor', location: 'New Jersey', target: 25 },
    { industry: 'Dentist', location: 'New York', target: 15 },
    { industry: 'Plumber', location: 'California', target: 30 },
  ];

  demoHunts.forEach((data, index) => {
    const huntId = `hunt_demo_${index + 1}`;
    const leads = generateMockLeads(data.target, data.industry);
    const ceoCount = leads.filter(l => l.decision_maker?.status === 'valid').length;
    const linkedinCount = leads.filter(l => l.decision_maker?.linkedin_url).length;

    const hunt: HuntDetails = {
      hunt_id: huntId,
      industry: data.industry,
      location: data.location,
      target: data.target,
      status: 'completed',
      created_at: new Date(Date.now() - (index + 1) * 24 * 60 * 60 * 1000).toISOString(),
      completed_at: new Date(Date.now() - (index + 1) * 24 * 60 * 60 * 1000 + 120000).toISOString(),
      leads,
      total_leads: leads.length,
      stats: {
        total_leads: leads.length,
        ceos_found: ceoCount,
        linkedin_found: linkedinCount,
        cost: ceoCount * 0.04,
      },
      performance: {
        total_time: 105,
        stage1_time: 33,
        stage2_time: 62,
        stage3_time: 10,
      },
    };

    store.hunts.set(huntId, hunt);
  });
}

// Initialize with demo data
seedDemoData();
