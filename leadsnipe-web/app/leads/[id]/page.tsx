'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';

export default function LeadDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [isFavorite, setIsFavorite] = useState(false);

  const [lead, setLead] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generatingEmail, setGeneratingEmail] = useState(false);
  const [showDraft, setShowDraft] = useState(false);

  useEffect(() => {
    async function fetchLead() {
      try {
        const data = await api.getLeads(); // Fetch all and filter for now
        const found = (data.leads || []).find((l: any) => l.id === params.id);
        setLead(found || null);
      } catch (err) {
        console.error('Failed to fetch lead:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchLead();
  }, [params.id]);

  const handleGenerateEmail = async () => {
    setGeneratingEmail(true);
    try {
      // Small timeout to simulate AI work if draft already exists
      await new Promise(r => setTimeout(r, 2000));
      setShowDraft(true);
    } catch (err) {
      console.error('Email generation failed:', err);
    } finally {
      setGeneratingEmail(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors = {
      new: 'bg-blue-100 text-blue-800',
      contacted: 'bg-yellow-100 text-yellow-800',
      replied: 'bg-green-100 text-green-800',
      meeting_booked: 'bg-purple-100 text-purple-800',
    };
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const getStatusLabel = (status: string) => {
    const labels = {
      new: 'New Lead',
      contacted: 'Email Sent',
      replied: 'Replied',
      meeting_booked: 'Meeting Booked',
    };
    return labels[status as keyof typeof labels] || status;
  };

  return (
    <div className="min-h-screen bg-background-light">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <Link href="/leads" className="text-brand-blue hover:text-blue-700 font-semibold transition-colors">
              ← Back to Leads
            </Link>
            <h1 className="text-xl font-bold text-primary">Lead Details</h1>
            <button
              onClick={() => setIsFavorite(!isFavorite)}
              className="text-2xl hover:scale-110 transition-transform"
            >
              {isFavorite ? '⭐' : '☆'}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Loading State */}
        {loading && (
          <div className="flex justify-center py-20">
            <div className="w-12 h-12 border-4 border-brand-blue border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {!loading && !lead && (
          <div className="text-center py-20">
            <p className="text-gray-500">Lead not found</p>
          </div>
        )}

        {lead && (
          <>
            {/* Company Info */}
            <div className="bg-white border-b-2 border-gray-200 rounded-t-2xl p-6 shadow-sm">
              <h2 className="text-3xl font-bold text-primary mb-3">{lead.name}</h2>
              <div className="flex items-center mb-4">
                <div className="w-8 h-8 bg-gray-50 rounded-lg flex items-center justify-center mr-2">
                  <span>📍</span>
                </div>
                <p className="text-gray-600 font-medium">{lead.address || 'Unknown Location'}</p>
              </div>
              <span
                className={`inline-block px-4 py-2 rounded-full text-sm font-bold ${getStatusColor(
                  lead.status || 'new'
                )}`}
              >
                {getStatusLabel(lead.status || 'new')}
              </span>
            </div>

            {/* Decision Maker */}
            <div className="card mt-6">
              <h3 className="text-xl font-bold text-primary mb-4">Decision Maker</h3>
              <div className="space-y-3">
                <div className="flex justify-between pb-3 border-b-2 border-gray-200">
                  <span className="text-gray-600">Name</span>
                  <span className="font-bold text-primary">{lead.decisionMaker}</span>
                </div>
                <div className="flex justify-between pb-3 border-b-2 border-gray-200">
                  <span className="text-gray-600">Title</span>
                  <span className="font-bold text-primary">{lead.title}</span>
                </div>
                <div className="flex justify-between pb-3 border-b-2 border-gray-200">
                  <span className="text-gray-600">Email</span>
                  <a
                    href={`mailto:${lead.email}`}
                    className="font-bold text-brand-blue hover:text-blue-700 transition-colors"
                  >
                    {lead.email}
                  </a>
                </div>
                {lead.linkedin && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">LinkedIn</span>
                    <a
                      href={lead.linkedin}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-bold text-brand-blue hover:text-blue-700 transition-colors"
                    >
                      View Profile →
                    </a>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="card mt-6">
              <h3 className="text-xl font-bold text-primary mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <button
                  onClick={handleGenerateEmail}
                  disabled={generatingEmail}
                  className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-brand-blue hover:text-white rounded-xl transition-all duration-200 group disabled:opacity-50"
                >
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center mr-3 group-hover:bg-white/20 transition-colors">
                      <span className={`text-2xl ${generatingEmail ? 'animate-spin' : ''}`}>
                        {generatingEmail ? '⏳' : '✉️'}
                      </span>
                    </div>
                    <span className="font-bold text-primary group-hover:text-white transition-colors">
                      {generatingEmail ? 'Analyzing Website...' : 'Generate AI Email'}
                    </span>
                  </div>
                  <span className="text-gray-400 group-hover:text-white transition-colors">→</span>
                </button>

                {showDraft && lead.email_draft && (
                  <div className="bg-blue-50 border-2 border-blue-200 rounded-2xl p-6 mt-4 animate-in fade-in slide-in-from-top-4 duration-500">
                    <div className="flex justify-between items-center mb-4">
                      <h4 className="font-bold text-blue-900">AI Sample Draft</h4>
                      <button className="text-xs font-bold text-brand-blue uppercase">Edit Draft</button>
                    </div>
                    <p className="text-sm font-bold text-blue-900 mb-2">Subject: {lead.email_draft.subject}</p>
                    <p className="text-sm text-blue-800 whitespace-pre-line bg-white/50 p-4 rounded-xl border border-blue-100">
                      {lead.email_draft.body}
                    </p>
                    <button className="btn-primary w-full mt-4 flex items-center justify-center gap-2">
                      <span>🚀</span> Send via Gmail
                    </button>
                  </div>
                )}

                <a
                  href={`mailto:${lead.email}`}
                  className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-brand-blue hover:text-white rounded-xl transition-all duration-200 group"
                >
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center mr-3 group-hover:bg-white/20 transition-colors">
                      <span className="text-2xl">📧</span>
                    </div>
                    <span className="font-bold text-primary group-hover:text-white transition-colors">Send Email Directly</span>
                  </div>
                  <span className="text-gray-400 group-hover:text-white transition-colors">→</span>
                </a>

                <a
                  href={lead.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-brand-blue hover:text-white rounded-xl transition-all duration-200 group"
                >
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center mr-3 group-hover:bg-white/20 transition-colors">
                      <span className="text-2xl">💼</span>
                    </div>
                    <span className="font-bold text-primary group-hover:text-white transition-colors">View on LinkedIn</span>
                  </div>
                  <span className="text-gray-400 group-hover:text-white transition-colors">→</span>
                </a>

                <button className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-brand-blue hover:text-white rounded-xl transition-all duration-200 group">
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center mr-3 group-hover:bg-white/20 transition-colors">
                      <span className="text-2xl">🔄</span>
                    </div>
                    <span className="font-bold text-primary group-hover:text-white transition-colors">Refresh Data</span>
                  </div>
                  <span className="text-gray-400 group-hover:text-white transition-colors">→</span>
                </button>

                <button className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-brand-green hover:text-white rounded-xl transition-all duration-200 group">
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center mr-3 group-hover:bg-white/20 transition-colors">
                      <span className="text-2xl">✓</span>
                    </div>
                    <span className="font-bold text-primary group-hover:text-white transition-colors">Verify Email</span>
                  </div>
                  <span className="text-gray-400 group-hover:text-white transition-colors">→</span>
                </button>
              </div>
            </div>

            {/* Additional Information */}
            <div className="card mt-6">
              <h3 className="text-xl font-bold text-primary mb-4">Additional Information</h3>
              <div className="space-y-3">
                <div className="flex justify-between pb-3 border-b-2 border-gray-200">
                  <span className="text-gray-600">Phone</span>
                  <span className="font-bold text-primary">{lead.phone || 'Not available'}</span>
                </div>
                <div className="flex justify-between pb-3 border-b-2 border-gray-200">
                  <span className="text-gray-600">Website</span>
                  <a
                    href={lead.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-bold text-brand-blue hover:text-blue-700 transition-colors"
                  >
                    {lead.website}
                  </a>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Industry</span>
                  <span className="font-bold text-primary">{lead.industry}</span>
                </div>
              </div>
            </div>

            {/* Activity History */}
            <div className="card mt-6">
              <h3 className="text-xl font-bold text-primary mb-4">Activity History</h3>
              <div className="space-y-4">
                <div className="flex items-start">
                  <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center mr-3 flex-shrink-0">
                    <span className="text-2xl">🎯</span>
                  </div>
                  <div>
                    <p className="text-primary font-bold">Lead created</p>
                    <p className="text-sm text-gray-500 font-medium">Today at 2:15 PM</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Action */}
            <div className="mt-6">
              <button
                onClick={handleGenerateEmail}
                disabled={generatingEmail}
                className="btn-primary w-full"
              >
                {generatingEmail ? 'Generating...' : 'Generate AI Email'}
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
