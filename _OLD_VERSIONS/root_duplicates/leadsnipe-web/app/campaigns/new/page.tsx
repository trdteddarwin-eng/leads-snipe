'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

export default function NewCampaignPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  // Campaign data
  const [campaignName, setCampaignName] = useState('');
  const [industry, setIndustry] = useState('');
  const [location, setLocation] = useState('');
  const [targetLeads, setTargetLeads] = useState(25);
  const [emailSubject, setEmailSubject] = useState('Question about your {businessType} service');
  const [emailBody, setEmailBody] = useState(
    `Hi {firstName},\n\nI noticed {company} while researching {businessType} businesses in {city}.\n\nQuick question: How do you currently handle after-hours calls and customer inquiries?\n\nI work with local businesses to implement AI-powered receptionists that can:\n• Answer common questions 24/7\n• Book appointments automatically\n• Capture leads even when you're busy\n\nWould you be open to a quick 15-min call to see if this makes sense for {company}?\n\nBest,\n[Your Name]`
  );

  const suggestedIndustries = [
    'HVAC', 'Dentist', 'Med Spa', 'Plumber', 'Electrician',
    'Real Estate', 'Restaurant', 'Law Firm', 'Accounting',
  ];

  const leadCountOptions = [
    { value: 10, label: '10 Leads', subtitle: 'Quick test' },
    { value: 25, label: '25 Leads', subtitle: 'Recommended' },
    { value: 50, label: '50 Leads', subtitle: 'Medium campaign' },
    { value: 100, label: '100 Leads', subtitle: 'Large campaign' },
  ];

  const [huntId, setHuntId] = useState<string | null>(null);
  const [huntStatus, setHuntStatus] = useState<any>(null);
  const [logs, setLogs] = useState<string[]>([]);

  const handleLaunchCampaign = async () => {
    setLoading(true);
    setStep(5); // Move to a "Processing" step
    try {
      const resp = await api.startHunt({
        niche: industry,
        location: location,
        limit: targetLeads,
      });

      setHuntId(resp.hunt_id);

      // Start polling for status
      const pollInterval = setInterval(async () => {
        try {
          const status = await api.getHuntStatus(resp.hunt_id);
          setHuntStatus(status);

          if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(pollInterval);
            if (status.status === 'completed') {
              setTimeout(() => {
                router.push('/leads');
              }, 3000);
            }
          }
        } catch (err) {
          console.error('Polling error:', err);
        }
      }, 2000);

      // Connect to logs
      const eventSource = api.getLogSource(resp.hunt_id);
      eventSource.onmessage = (event) => {
        const dataArr = JSON.parse(event.data);
        if (Array.isArray(dataArr)) {
          setLogs(prev => [...prev, ...dataArr.map(l => l.message)].slice(-50));
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
      };

    } catch (error: any) {
      console.error('Campaign launch error:', error);
      alert(error.message || 'Failed to launch campaign');
      setStep(4);
    } finally {
      setLoading(false);
    }
  };

  const estimatedCost = (targetLeads * 0.4 * 0.04).toFixed(2);

  return (
    <div className="min-h-screen bg-background-light">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <button
              onClick={() => (step > 1 ? setStep(step - 1) : router.push('/dashboard'))}
              className="text-brand-blue hover:text-blue-700 font-semibold transition-colors"
            >
              ← Back
            </button>
            <h1 className="text-xl font-bold text-primary">New Campaign</h1>
            <div className="w-16" />
          </div>
        </div>
      </header>

      {/* Progress Bar */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="h-2 bg-gray-200 rounded-full mb-2">
            <div
              className="h-full bg-gradient-to-r from-brand-blue to-indigo-600 rounded-full transition-all"
              style={{ width: `${(step / 4) * 100}%` }}
            />
          </div>
          <p className="text-sm text-center text-gray-600 font-medium">Step {step} of 4</p>
        </div>
      </div>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Step 1: Campaign Setup */}
        {step === 1 && (
          <div>
            <h2 className="text-2xl font-bold text-primary mb-2">Campaign Setup</h2>
            <p className="text-gray-600 mb-6">Tell us about your target audience</p>

            <div className="card space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Campaign Name
                </label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="e.g., Newark HVAC Outreach"
                  value={campaignName}
                  onChange={(e) => setCampaignName(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Industry / Business Type
                </label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="e.g., HVAC, Dentist, Med Spa"
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                />
                <div className="flex flex-wrap gap-2 mt-3">
                  {suggestedIndustries.map((ind) => (
                    <button
                      key={ind}
                      onClick={() => setIndustry(ind)}
                      className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 ${industry === ind
                        ? 'bg-brand-blue text-white shadow-md'
                        : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 hover:border-brand-blue'
                        }`}
                    >
                      {ind}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Location
                </label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="e.g., Newark, New Jersey"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                />
                <p className="text-sm text-gray-500 mt-1">
                  Enter city and state for best results
                </p>
              </div>

              <div className="bg-blue-50 border-2 border-blue-200 rounded-2xl p-5">
                <div className="flex items-start">
                  <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center mr-3 flex-shrink-0">
                    <span className="text-2xl">ℹ️</span>
                  </div>
                  <div>
                    <h4 className="font-bold text-blue-900 mb-1">How it works</h4>
                    <p className="text-sm text-blue-800">
                      LeadSnipe will scrape Google Maps for businesses matching your criteria,
                      then enrich each lead with decision maker contact info and LinkedIn profiles.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6">
              <button
                onClick={() => setStep(2)}
                disabled={!campaignName || !industry || !location}
                className="btn-primary w-full disabled:opacity-40"
              >
                Continue
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Lead Criteria */}
        {step === 2 && (
          <div>
            <h2 className="text-2xl font-bold text-primary mb-2">Lead Criteria</h2>
            <p className="text-gray-600 mb-6">How many leads do you want to generate?</p>

            <div className="space-y-4 mb-6">
              {leadCountOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setTargetLeads(option.value)}
                  className={`w-full card text-left transition-all duration-200 ${targetLeads === option.value
                    ? 'border-2 border-brand-blue bg-blue-50 shadow-lg'
                    : 'border border-gray-200 hover:border-brand-blue hover:shadow-md'
                    }`}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <div className={`text-lg font-bold ${targetLeads === option.value ? 'text-brand-blue' : 'text-primary'
                        }`}>
                        {option.label}
                      </div>
                      <div className="text-gray-600 text-sm">{option.subtitle}</div>
                    </div>
                    <div className={`w-7 h-7 rounded-full border-2 flex items-center justify-center transition-all ${targetLeads === option.value
                      ? 'border-brand-blue bg-brand-blue'
                      : 'border-gray-300'
                      }`}>
                      {targetLeads === option.value && (
                        <div className="w-3 h-3 bg-white rounded-full" />
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>

            <div className="card mb-6">
              <h3 className="font-bold text-primary mb-4">Estimated Cost</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Lead Scraping</span>
                  <span className="font-bold text-brand-green">FREE</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Decision Maker Emails</span>
                  <span className="font-bold text-primary">~${estimatedCost}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">LinkedIn Discovery</span>
                  <span className="font-bold text-brand-green">FREE</span>
                </div>
                <div className="border-t-2 border-gray-200 my-2" />
                <div className="flex justify-between items-center">
                  <span className="font-bold text-primary">Total Estimated Cost</span>
                  <span className="font-bold text-brand-blue text-xl">~${estimatedCost}</span>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-4 italic">
                * Only charged for successfully found decision maker emails (~40% success rate)
              </p>
            </div>

            <button onClick={() => setStep(3)} className="btn-primary w-full">
              Continue
            </button>
          </div>
        )}

        {/* Step 3: Email Template */}
        {step === 3 && (
          <div>
            <h2 className="text-2xl font-bold text-primary mb-2">Email Template</h2>
            <p className="text-gray-600 mb-6">Customize your outreach message</p>

            <div className="card space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Subject Line
                </label>
                <input
                  type="text"
                  className="input-field"
                  value={emailSubject}
                  onChange={(e) => setEmailSubject(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Body
                </label>
                <textarea
                  className="input-field min-h-[300px]"
                  value={emailBody}
                  onChange={(e) => setEmailBody(e.target.value)}
                />
              </div>

              <div>
                <h4 className="text-sm font-bold text-gray-700 mb-2">
                  Personalization Variables (tap to insert)
                </h4>
                <div className="flex flex-wrap gap-2">
                  {['firstName', 'lastName', 'fullName', 'company', 'businessType', 'city', 'address', 'website'].map(
                    (variable) => (
                      <button
                        key={variable}
                        onClick={() => setEmailBody(emailBody + ` {${variable}}`)}
                        className="px-3 py-1.5 bg-blue-50 border border-blue-200 text-brand-blue text-sm rounded-full hover:bg-brand-blue hover:text-white transition-all duration-200 font-medium"
                      >
                        {`{${variable}}`}
                      </button>
                    )
                  )}
                </div>
              </div>

              <div className="bg-gray-50 border-2 border-gray-200 rounded-2xl p-5">
                <h4 className="font-bold text-primary mb-3">Preview Example</h4>
                <p className="text-sm font-bold text-gray-700 mb-2">
                  {emailSubject.replace('{businessType}', industry)}
                </p>
                <p className="text-sm text-gray-600 whitespace-pre-line">
                  {emailBody
                    .replace('{firstName}', 'John')
                    .replace('{company}', 'ABC Company')
                    .replace(/{businessType}/g, industry)
                    .replace('{city}', location.split(',')[0] || location)
                    .substring(0, 200) + '...'}
                </p>
              </div>
            </div>

            <div className="mt-6">
              <button onClick={() => setStep(4)} className="btn-primary w-full">
                Continue
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Review & Launch */}
        {step === 4 && (
          <div>
            <h2 className="text-2xl font-bold text-primary mb-2">Review & Launch</h2>
            <p className="text-gray-600 mb-6">Review your campaign settings before launching</p>

            <div className="space-y-4">
              <div className="card">
                <h3 className="font-bold text-primary mb-4">Campaign Details</h3>
                <div className="space-y-3">
                  <div className="flex justify-between pb-3 border-b-2 border-gray-200">
                    <span className="text-gray-600">Name</span>
                    <span className="font-bold text-primary">{campaignName}</span>
                  </div>
                  <div className="flex justify-between pb-3 border-b-2 border-gray-200">
                    <span className="text-gray-600">Industry</span>
                    <span className="font-bold text-primary">{industry}</span>
                  </div>
                  <div className="flex justify-between pb-3 border-b-2 border-gray-200">
                    <span className="text-gray-600">Location</span>
                    <span className="font-bold text-primary">{location}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Target Leads</span>
                    <span className="font-bold text-primary">{targetLeads} leads</span>
                  </div>
                </div>
              </div>

              <div className="card">
                <h3 className="font-bold text-primary mb-4">Email Template</h3>
                <div className="bg-gray-50 rounded-2xl p-4">
                  <p className="text-xs text-gray-500 mb-1 font-medium">Subject:</p>
                  <p className="font-bold text-primary mb-3">{emailSubject}</p>
                  <p className="text-xs text-gray-500 mb-1 font-medium">Body:</p>
                  <p className="text-sm text-gray-600 whitespace-pre-line line-clamp-6">
                    {emailBody}
                  </p>
                </div>
              </div>

              <div className="bg-blue-50 border-2 border-blue-200 rounded-2xl p-5">
                <div className="flex items-start">
                  <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center mr-3 flex-shrink-0">
                    <span className="text-3xl">🚀</span>
                  </div>
                  <div>
                    <h4 className="font-bold text-blue-900 mb-2">What happens next?</h4>
                    <p className="text-sm text-blue-800 leading-relaxed">
                      1. LeadSnipe will scrape {targetLeads} {industry} businesses in {location}<br />
                      2. Find decision maker emails for each business<br />
                      3. Discover LinkedIn profiles<br />
                      4. All leads will appear in your dashboard ready for outreach
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-center bg-gray-50 border-2 border-gray-200 rounded-2xl p-4">
                <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center mr-3">
                  <span className="text-2xl">⏱️</span>
                </div>
                <span className="text-sm text-gray-700 font-medium">
                  Estimated completion: {Math.ceil(targetLeads / 10)} - {Math.ceil(targetLeads / 5)} minutes
                </span>
              </div>
            </div>

            <div className="mt-6">
              <button
                onClick={handleLaunchCampaign}
                disabled={loading}
                className="btn-success w-full disabled:opacity-60 text-lg"
              >
                {loading ? 'Launching Campaign...' : '🚀 Launch Campaign'}
              </button>
            </div>
          </div>
        )}

        {/* Step 5: Progress Radar */}
        {step === 5 && (
          <div className="flex flex-col items-center justify-center py-12">
            <div className="relative mb-12">
              <div className="w-64 h-64 border-4 border-brand-blue/20 rounded-full animate-ping absolute" />
              <div className="w-64 h-64 border-4 border-brand-blue rounded-full flex flex-col items-center justify-center bg-white shadow-2xl relative z-10 transition-all">
                <span className="text-4xl mb-2">{huntStatus?.status === 'completed' ? '✅' : '📡'}</span>
                <span className="text-2xl font-bold text-primary">{huntStatus?.progress_percent || 0}%</span>
                <span className="text-xs text-gray-400 font-bold uppercase tracking-widest mt-1">
                  {huntStatus?.status || 'INITIALIZING'}
                </span>
              </div>
            </div>

            <div className="w-full max-w-lg">
              <h3 className="text-center font-bold text-xl text-primary mb-2">
                {huntStatus?.stage_message || 'Initializing pipeline...'}
              </h3>
              <p className="text-center text-gray-500 mb-8">
                The LeadSnipe engine is deep-crawling the web for you.
              </p>

              <div className="grid grid-cols-3 gap-4 mb-8">
                <div className="card text-center py-4">
                  <p className="text-2xl mb-1">🏢</p>
                  <p className="text-sm font-bold text-primary">{huntStatus?.leads_found || 0}</p>
                  <p className="text-[10px] text-gray-400 uppercase font-bold">Leads</p>
                </div>
                <div className="card text-center py-4">
                  <p className="text-2xl mb-1">👤</p>
                  <p className="text-sm font-bold text-primary">{huntStatus?.owners_found || 0}</p>
                  <p className="text-[10px] text-gray-400 uppercase font-bold">Owners</p>
                </div>
                <div className="card text-center py-4">
                  <p className="text-2xl mb-1">✉️</p>
                  <p className="text-sm font-bold text-primary">{huntStatus?.emails_found || 0}</p>
                  <p className="text-[10px] text-gray-400 uppercase font-bold">Emails</p>
                </div>
              </div>

              {/* Log Stream */}
              <div className="bg-black rounded-2xl p-6 font-mono text-xs text-brand-green h-64 overflow-y-auto shadow-2xl border border-gray-800">
                <div className="flex items-center gap-2 mb-4 border-b border-gray-800 pb-2">
                  <div className="w-2 h-2 bg-brand-green rounded-full animate-pulse" />
                  <span className="text-gray-500 font-bold">SYSTEM LOGS</span>
                </div>
                {logs.length === 0 ? (
                  <p className="text-gray-600 animate-pulse">Waiting for hunt logs...</p>
                ) : (
                  logs.map((log, i) => (
                    <div key={i} className="mb-1 opacity-80 hover:opacity-100 transition-opacity">
                      <span className="text-gray-600 mr-2">[{new Date().toLocaleTimeString([], { hour12: false })}]</span>
                      {log}
                    </div>
                  ))
                )}
              </div>

              {huntStatus?.status === 'completed' && (
                <div className="mt-8">
                  <button onClick={() => router.push('/leads')} className="btn-primary w-full shadow-brand-blue/20 shadow-xl">
                    View Results 🚀
                  </button>
                </div>
              )}

              {huntStatus?.status === 'failed' && (
                <div className="mt-8 text-center">
                  <p className="text-red-500 font-bold mb-4">Error: {huntStatus.error}</p>
                  <button onClick={() => setStep(4)} className="btn-secondary w-full">
                    Go Back & Try Again
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
