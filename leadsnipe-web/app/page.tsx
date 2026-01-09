'use client';

import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <header className="border-b border-gray-100 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-brand-blue rounded-xl flex items-center justify-center">
                <span className="text-white text-2xl font-bold">L</span>
              </div>
              <h1 className="text-2xl font-bold text-primary">LeadSnipe</h1>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => router.push('/login')}
                className="px-6 py-2 text-gray-700 hover:text-gray-900 font-medium transition-colors"
              >
                Sign In
              </button>
              <button
                onClick={() => router.push('/signup')}
                className="btn-primary"
              >
                Get Started
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center max-w-4xl mx-auto">
          <div className="inline-block mb-4 px-4 py-2 bg-blue-50 rounded-full">
            <span className="text-brand-blue font-semibold text-sm">✨ AI-Powered Lead Generation</span>
          </div>

          <h1 className="text-6xl md:text-7xl font-bold text-primary mb-6 leading-tight">
            Find Decision Makers<br />
            <span className="bg-gradient-to-r from-brand-blue to-indigo-600 bg-clip-text text-transparent">
              Close More Deals
            </span>
          </h1>

          <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
            Generate high-quality B2B leads with verified decision maker emails and LinkedIn profiles.
            Automate your outreach and grow faster.
          </p>

          <div className="flex gap-4 justify-center mb-6">
            <button
              onClick={() => router.push('/signup')}
              className="btn-primary text-lg px-8 py-4 animate-bounce-in"
            >
              Start Free Trial
            </button>
            <button
              onClick={() => router.push('/login')}
              className="btn-secondary text-lg px-8 py-4"
            >
              Watch Demo
            </button>
          </div>

          <div className="text-sm text-gray-500">
            💳 No credit card required • ⚡ 2-minute setup
          </div>
        </div>

        {/* Stats */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          <div className="text-center animate-slide-up">
            <div className="text-4xl font-bold text-brand-blue mb-2">70-85%</div>
            <div className="text-gray-600">Success Rate</div>
          </div>
          <div className="text-center animate-slide-up" style={{animationDelay: '0.1s'}}>
            <div className="text-4xl font-bold text-brand-green mb-2">$0.02</div>
            <div className="text-gray-600">Per Enriched Lead</div>
          </div>
          <div className="text-center animate-slide-up" style={{animationDelay: '0.2s'}}>
            <div className="text-4xl font-bold text-purple-600 mb-2">19+</div>
            <div className="text-gray-600">Data Points</div>
          </div>
        </div>

        {/* Features */}
        <div className="mt-32">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-primary mb-4">Everything you need to scale</h2>
            <p className="text-xl text-gray-600">Powerful features that help you find and close more leads</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="card group hover:border-brand-blue cursor-pointer">
              <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center mb-4 group-hover:bg-brand-blue transition-colors">
                <span className="text-3xl group-hover:scale-110 transition-transform">🎯</span>
              </div>
              <h3 className="text-xl font-bold text-primary mb-2">Smart Targeting</h3>
              <p className="text-gray-600">
                AI-powered lead discovery finds the perfect prospects in your target industry and location
              </p>
            </div>

            <div className="card group hover:border-brand-green cursor-pointer">
              <div className="w-12 h-12 bg-green-50 rounded-xl flex items-center justify-center mb-4 group-hover:bg-brand-green transition-colors">
                <span className="text-3xl group-hover:scale-110 transition-transform">📧</span>
              </div>
              <h3 className="text-xl font-bold text-primary mb-2">Decision Maker Emails</h3>
              <p className="text-gray-600">
                Get verified CEO and owner emails for direct outreach that actually converts
              </p>
            </div>

            <div className="card group hover:border-purple-500 cursor-pointer">
              <div className="w-12 h-12 bg-purple-50 rounded-xl flex items-center justify-center mb-4 group-hover:bg-purple-500 transition-colors">
                <span className="text-3xl group-hover:scale-110 transition-transform">💼</span>
              </div>
              <h3 className="text-xl font-bold text-primary mb-2">LinkedIn Profiles</h3>
              <p className="text-gray-600">
                Discover LinkedIn profiles automatically for powerful multi-channel engagement
              </p>
            </div>
          </div>
        </div>

        {/* How It Works */}
        <div className="mt-32 bg-white rounded-3xl shadow-xl p-12">
          <h2 className="text-4xl font-bold text-primary mb-12 text-center">How It Works</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-brand-blue text-white rounded-2xl flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                1
              </div>
              <h3 className="text-xl font-bold text-primary mb-2">Create Campaign</h3>
              <p className="text-gray-600">
                Choose your target industry and location in seconds
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-brand-green text-white rounded-2xl flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                2
              </div>
              <h3 className="text-xl font-bold text-primary mb-2">Auto-Enrich</h3>
              <p className="text-gray-600">
                AI finds decision makers and LinkedIn profiles automatically
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-purple-600 text-white rounded-2xl flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                3
              </div>
              <h3 className="text-xl font-bold text-primary mb-2">Close Deals</h3>
              <p className="text-gray-600">
                Send personalized emails and book more meetings
              </p>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-32 text-center bg-gradient-to-r from-brand-blue to-indigo-600 rounded-3xl p-16 text-white">
          <h2 className="text-4xl font-bold mb-4">Ready to generate better leads?</h2>
          <p className="text-xl mb-8 opacity-90">Join thousands of sales teams closing more deals with LeadSnipe</p>
          <button
            onClick={() => router.push('/signup')}
            className="bg-white text-brand-blue hover:bg-gray-100 font-bold text-lg px-10 py-4 rounded-xl transition-all shadow-2xl hover:scale-105"
          >
            Start Free Trial →
          </button>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 mt-32 py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-gray-600">
          <p>© 2026 LeadSnipe. AI-Powered B2B Lead Generation.</p>
        </div>
      </footer>
    </div>
  );
}
