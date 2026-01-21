'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';

export default function DashboardPage() {
  const [stats, setStats] = useState({
    totalLeads: 0,
    qualified: 0,
    avgScore: 0,
    conversion: 0,
    trends: {
      leads: 0,
      qualified: 0,
      score: 0,
      conversion: 0,
    },
  });

  const [recentActivity, setRecentActivity] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const leadsData = await api.getLeads();
        const leads = leadsData.leads || [];

        const ownersFound = leads.filter((l: any) => l.owner_name).length;
        const emailsFound = leads.filter((l: any) => l.anymailfinder_email).length;

        setStats({
          totalLeads: leads.length,
          qualified: emailsFound,
          avgScore: Math.round((ownersFound / (leads.length || 1)) * 100),
          conversion: Math.round((emailsFound / (leads.length || 1)) * 100),
          trends: { leads: 12, qualified: 8, score: 3, conversion: 5 } // Placeholder trends
        });

        // Mock recent activity from leads
        const activity = leads.slice(0, 5).map((l: any) => ({
          id: l.id,
          type: 'new',
          message: `Lead discovered: ${l.name}`,
          time: 'Just now',
          icon: '🏢'
        }));
        setRecentActivity(activity);
      } catch (err) {
        console.error('Dashboard fetch error:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const [activeNav, setActiveNav] = useState('overview');

  return (
    <div className="min-h-screen bg-white flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-brand-blue rounded-lg flex items-center justify-center">
              <span className="text-white text-xl font-bold">L</span>
            </div>
            <span className="text-xl font-bold text-primary">LeadSnipe</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <div className="space-y-1">
            <button
              onClick={() => setActiveNav('overview')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeNav === 'overview'
                  ? 'bg-blue-50 text-brand-blue font-semibold'
                  : 'text-gray-700 hover:bg-gray-50'
                }`}
            >
              <span className="text-xl">📊</span>
              <span>Overview</span>
            </button>

            <Link
              href="/leads"
              className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-50 transition-all"
            >
              <span className="text-xl">👥</span>
              <span>Leads</span>
            </Link>

            <button
              onClick={() => setActiveNav('analytics')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeNav === 'analytics'
                  ? 'bg-blue-50 text-brand-blue font-semibold'
                  : 'text-gray-700 hover:bg-gray-50'
                }`}
            >
              <span className="text-xl">📈</span>
              <span>Analytics</span>
            </button>

            <button
              onClick={() => setActiveNav('settings')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeNav === 'settings'
                  ? 'bg-blue-50 text-brand-blue font-semibold'
                  : 'text-gray-700 hover:bg-gray-50'
                }`}
            >
              <span className="text-xl">⚙️</span>
              <span>Settings</span>
            </button>
          </div>
        </nav>

        {/* Upgrade Plan CTA */}
        <div className="p-4">
          <div className="bg-brand-blue rounded-2xl p-5 text-white">
            <p className="text-xs font-semibold mb-2 opacity-90">UPGRADE PLAN</p>
            <p className="font-bold text-lg mb-4">Snipe Premium</p>
            <button className="w-full bg-white text-brand-blue font-bold py-2.5 px-4 rounded-lg hover:bg-blue-50 transition-colors text-sm">
              Get 2× Credits
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Header */}
        <header className="bg-white border-b border-gray-200 px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-primary">LeadSnipe Dashboard</h1>
            <div className="flex items-center gap-4">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search leads, companies..."
                  className="w-80 pl-4 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-blue focus:border-transparent"
                />
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
              </div>
              <button className="w-10 h-10 bg-gray-50 hover:bg-gray-100 rounded-lg flex items-center justify-center transition-colors">
                🌙
              </button>
              <button className="relative p-2 hover:bg-gray-50 rounded-lg transition-colors">
                <span className="text-xl">🔔</span>
                <span className="absolute top-1 right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center font-semibold">
                  2
                </span>
              </button>
              <div className="w-10 h-10 bg-brand-blue rounded-full flex items-center justify-center text-white font-bold cursor-pointer hover:scale-105 transition-transform">
                JD
              </div>
            </div>
          </div>
        </header>

        {/* Main Dashboard Content */}
        <main className="flex-1 overflow-y-auto bg-gray-50 p-8">
          {/* Welcome Message */}
          <div className="mb-6">
            <h2 className="text-3xl font-bold text-primary mb-2">Sales Overview</h2>
            <p className="text-gray-600">Welcome back, Sarah. Here's what's happening today.</p>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-4 gap-6 mb-8">
            {/* Total Leads */}
            <div className="bg-white rounded-2xl p-6 border border-gray-200 hover:shadow-lg transition-shadow">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0">
                  <span className="text-2xl">👥</span>
                </div>
                <div className="flex-1">
                  <p className="text-gray-600 text-sm mb-1">Total Leads</p>
                  <p className="text-3xl font-bold text-primary mb-2">{stats.totalLeads.toLocaleString()}</p>
                  <div className="flex items-center text-sm">
                    <span className="text-brand-green font-semibold">+{stats.trends.leads}%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Qualified */}
            <div className="bg-white rounded-2xl p-6 border border-gray-200 hover:shadow-lg transition-shadow">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-purple-50 rounded-xl flex items-center justify-center flex-shrink-0">
                  <span className="text-2xl">⚙️</span>
                </div>
                <div className="flex-1">
                  <p className="text-gray-600 text-sm mb-1">Qualified</p>
                  <p className="text-3xl font-bold text-primary mb-2">{stats.qualified}</p>
                  <div className="flex items-center text-sm">
                    <span className="text-brand-green font-semibold">+{stats.trends.qualified}%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Avg. Score */}
            <div className="bg-white rounded-2xl p-6 border border-gray-200 hover:shadow-lg transition-shadow">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-green-50 rounded-xl flex items-center justify-center flex-shrink-0">
                  <span className="text-2xl">📊</span>
                </div>
                <div className="flex-1">
                  <p className="text-gray-600 text-sm mb-1">Avg. Score</p>
                  <p className="text-3xl font-bold text-primary mb-2">{stats.avgScore}</p>
                  <div className="flex items-center text-sm">
                    <span className="text-brand-green font-semibold">+{stats.trends.score}%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Conversion */}
            <div className="bg-white rounded-2xl p-6 border border-gray-200 hover:shadow-lg transition-shadow">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-orange-50 rounded-xl flex items-center justify-center flex-shrink-0">
                  <span className="text-2xl">🎯</span>
                </div>
                <div className="flex-1">
                  <p className="text-gray-600 text-sm mb-1">Conversion</p>
                  <p className="text-3xl font-bold text-primary mb-2">{stats.conversion}%</p>
                  <div className="flex items-center text-sm">
                    <span className="text-brand-green font-semibold">+{stats.trends.conversion}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-2 gap-6 mb-8">
            {/* Acquisition Flow Chart */}
            <div className="bg-white rounded-2xl p-6 border border-gray-200">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-bold text-primary">Acquisition Flow</h3>
                <select className="text-sm text-gray-600 bg-transparent border-0 focus:outline-none cursor-pointer">
                  <option>Last 7 Days</option>
                  <option>Last 30 Days</option>
                  <option>Last 90 Days</option>
                </select>
              </div>
              {/* Simple Chart Placeholder */}
              <div className="h-64 flex items-end justify-between gap-2">
                <div className="flex-1 bg-gradient-to-t from-brand-blue to-blue-400 rounded-t-lg" style={{ height: '40%' }}></div>
                <div className="flex-1 bg-gradient-to-t from-brand-blue to-blue-400 rounded-t-lg" style={{
                  height: '30%}}></div>
                    < div className="flex-1 bg-gradient-to-t from-brand-blue to-blue-400 rounded-t-lg" style={{height: '50%'}}></div>
              <div className="flex-1 bg-gradient-to-t from-brand-blue to-blue-400 rounded-t-lg" style={{ height: '65%' }}></div>
              <div className="flex-1 bg-gradient-to-t from-brand-blue to-blue-400 rounded-t-lg" style={{ height: '75%' }}></div>
              <div className="flex-1 bg-gradient-to-t from-brand-blue to-blue-400 rounded-t-lg" style={{ height: '90%' }}></div>
              <div className="flex-1 bg-gradient-to-t from-brand-blue to-blue-400 rounded-t-lg" style={{ height: '60%' }}></div>
            </div>
            <div className="flex justify-between mt-4 text-xs text-gray-500">
              <span>Mon</span>
              <span>Tue</span>
              <span>Wed</span>
              <span>Thu</span>
              <span>Fri</span>
              <span>Sat</span>
              <span>Sun</span>
            </div>
          </div>

          {/* Top Industries */}
          <div className="bg-white rounded-2xl p-6 border border-gray-200">
            <h3 className="text-lg font-bold text-primary mb-6">Top Industries</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">SaaS</span>
                  <span className="text-sm font-bold text-primary">45%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div className="bg-brand-blue rounded-full h-2" style={{ width: '45%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">Fintech</span>
                  <span className="text-sm font-bold text-primary">30%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div className="bg-brand-green rounded-full h-2" style={{ width: '30%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">Health</span>
                  <span className="text-sm font-bold text-primary">15%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div className="bg-yellow-500 rounded-full h-2" style={{ width: '15%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">Retail</span>
                  <span className="text-sm font-bold text-primary">10%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div className="bg-red-500 rounded-full h-2" style={{ width: '10%' }}></div>
                </div>
              </div>
            </div>
          </div>
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-xl font-bold text-primary mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 gap-4">
          <Link
            href="/campaigns/new"
            className="bg-white border border-gray-200 rounded-2xl p-5 hover:border-brand-blue hover:shadow-lg transition-all group"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center group-hover:bg-brand-blue transition-colors">
                <span className="text-2xl group-hover:scale-110 transition-transform">➕</span>
              </div>
              <div className="flex-1">
                <p className="font-bold text-primary mb-1">New Campaign</p>
                <p className="text-sm text-gray-600">Generate and enrich new leads</p>
              </div>
              <span className="text-gray-300 group-hover:text-brand-blue group-hover:translate-x-1 transition-all">→</span>
            </div>
          </Link>

          <Link
            href="/leads"
            className="bg-white border border-gray-200 rounded-2xl p-5 hover:border-brand-green hover:shadow-lg transition-all group"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-green-50 rounded-xl flex items-center justify-center group-hover:bg-brand-green transition-colors">
                <span className="text-2xl group-hover:scale-110 transition-transform">📋</span>
              </div>
              <div className="flex-1">
                <p className="font-bold text-primary mb-1">View All Leads</p>
                <p className="text-sm text-gray-600">Browse and manage your leads</p>
              </div>
              <span className="text-gray-300 group-hover:text-brand-green group-hover:translate-x-1 transition-all">→</span>
            </div>
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-primary">Recent Activity</h2>
          <button className="text-sm text-brand-blue hover:text-blue-700 font-semibold">
            See All →
          </button>
        </div>
        <div className="bg-white rounded-2xl border border-gray-200 p-6">
          <div className="space-y-4">
            {recentActivity.map((activity, index) => (
              <div
                key={activity.id}
                className={`flex items-start gap-4 ${index !== recentActivity.length - 1 ? 'pb-4 border-b border-gray-100' : ''
                  }`}
              >
                <div className="w-10 h-10 bg-gray-50 rounded-xl flex items-center justify-center flex-shrink-0">
                  <span className="text-xl">{activity.icon}</span>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-primary">{activity.message}</p>
                  <p className="text-xs text-gray-500 mt-1">{activity.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
      </div >
    </div >
  );
}
