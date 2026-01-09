"use client"

import * as React from "react"
import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { CTASection } from "@/components/ui/cta-with-rectangle"
import { IntelligenceCarousel } from "@/components/intelligence-carousel"
import { cn } from "@/lib/utils"

export default function LandingPage() {
    const [toastVisible, setToastVisible] = useState(false)
    const [toastText, setToastText] = useState("")
    const observerRef = useRef<IntersectionObserver | null>(null)

    // Scarcity Notification Logic
    useEffect(() => {
        const locations = ['Miami', 'New York', 'Sydney', 'London', 'Berlin', 'Toronto', 'Austin']

        const showNotification = () => {
            if (window.innerWidth < 768) return
            const loc = locations[Math.floor(Math.random() * locations.length)]
            setToastText(`Someone from ${loc} just started a new hunt.`)
            setToastVisible(true)
            setTimeout(() => setToastVisible(false), 5000)
        }

        const interval = setInterval(showNotification, 15000)
        const initialTimeout = setTimeout(showNotification, 3000)

        return () => {
            clearInterval(interval)
            clearTimeout(initialTimeout)
        }
    }, [])

    // Kinetic Typography Reveal
    useEffect(() => {
        observerRef.current = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    (entry.target as HTMLElement).style.animationPlayState = 'running'
                    observerRef.current?.unobserve(entry.target)
                }
            })
        }, { threshold: 0.1 })

        document.querySelectorAll('.kinetic-text').forEach(el => {
            (el as HTMLElement).style.animationPlayState = 'paused'
            observerRef.current?.observe(el)
        })

        return () => observerRef.current?.disconnect()
    }, [])

    return (
        <div className="min-h-screen bg-[#F5F5F4] text-[#0D0D14] selection:bg-[#7C3AED]/20">
            {/* Navigation */}
            <nav className="fixed top-0 left-0 w-full h-20 flex justify-between items-center px-[5%] bg-[#F5F5F4]/80 backdrop-blur-xl z-[1000] border-bottom border-black/5">
                <a href="#" className="flex items-center gap-3 font-bold text-xl no-underline text-[#0D0D14]">
                    <div className="w-10 h-10 bg-[#0D0D14] rounded-lg flex items-center justify-center text-white">🎯</div>
                    LeadSnipe
                </a>
                <div className="hidden md:flex gap-8">
                    <span className="no-underline text-[#0D0D14] text-sm font-medium opacity-70 cursor-default">Intelligence</span>
                    <span className="no-underline text-[#0D0D14] text-sm font-medium opacity-70 cursor-default">Process</span>
                    <span className="no-underline text-[#0D0D14] text-sm font-medium opacity-70 cursor-default">Investment</span>
                </div>
                <a href="/login" className="bg-[#0D0D14] text-white px-6 py-2.5 rounded-full text-sm font-semibold hover:scale-105 transition-transform">Sign In</a>
            </nav>

            {/* Hero Section */}
            <header className="relative min-h-screen flex flex-col items-center justify-center px-[5%] pt-32 pb-16 text-center overflow-hidden">
                {/* Floating Artifacts */}
                <div className="hidden lg:block">
                    <div className="artifact ceo-card absolute top-[15%] left-[5%] w-[280px] bg-white p-6 rounded-3xl shadow-glow border border-black/5 animate-float z-10">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 rounded-lg bg-[#7C3AED] text-white flex items-center justify-center font-bold">JD</div>
                            <div className="text-left">
                                <div className="text-sm font-bold">John Davidson</div>
                                <div className="text-[11px] opacity-60">CEO & Founder</div>
                            </div>
                        </div>
                        <div className="bg-[#DCFCE7] text-[#166534] text-[10px] font-bold px-3 py-1 rounded-md self-start">✓ DECISION MAKER</div>
                    </div>

                    <div className="artifact email-card absolute top-[10%] right-[5%] w-[260px] bg-white p-6 rounded-3xl shadow-glow border border-black/5 animate-float-delay z-10">
                        <div className="flex items-center gap-3 text-left">
                            <div className="text-xl">✉️</div>
                            <div className="text-sm font-semibold">Verified Direct Email</div>
                        </div>
                        <div className="text-[12px] opacity-60 text-left mt-2">john.davidson@dentalcare.com</div>
                    </div>
                </div>

                {/* Hero Content */}
                <div className="relative z-20 max-w-[1000px]">
                    <span className="hero-tag kinetic-text mb-6">The end of gatekeepers is here</span>
                    <h1 className="kinetic-text text-5xl md:text-8xl font-serif leading-[1.1] mb-6">
                        Stop emailing generic receptionists. <br />
                        <span className="text-[#7C3AED] block mt-4 font-sans text-lg md:text-2xl font-medium tracking-[0.2em] uppercase">Talk to decision makers directly.</span>
                    </h1>
                    <p className="kinetic-text text-lg md:text-xl text-[#0D0D14]/60 max-w-[600px] mx-auto mb-12 leading-relaxed">
                        LeadSnipe's AI-sentient discovery engine bypasses "info@" filters to pinpoint owners and CEOs who actually sign checks.
                    </p>

                    <form className="lead-form kinetic-text mx-auto w-full max-w-[500px] bg-white p-3 rounded-full flex gap-2 shadow-2xl border border-black/5 mb-8 focus-within:scale-105 transition-transform">
                        <input
                            type="email"
                            placeholder="Enter your business email"
                            className="flex-1 border-none bg-transparent px-6 py-2 outline-none text-[#0D0D14]"
                            required
                        />
                        <Button size="lg" className="rounded-full bg-[#7C3AED] hover:bg-[#8B5CF6] shadow-purple-500/30">Get Access</Button>
                    </form>

                    <div className="social-proof kinetic-text flex flex-col md:flex-row items-center justify-center gap-4 text-sm text-[#0D0D14]/50">
                        <div className="flex">
                            {[1, 2, 3, 4].map(i => (
                                <img key={i} src={`https://i.pravatar.cc/100?u=${i}`} className="w-8 h-8 rounded-full border-2 border-[#F5F5F4] -ml-2 first:ml-0" alt="" />
                            ))}
                        </div>
                        <span>Join 1,200+ agency owners closing deals faster.</span>
                    </div>
                </div>
            </header>

            {/* Logos Section */}
            <section className="py-20 px-[5%] bg-[#FAF9F6] border-y border-black/5 text-center">
                <p className="text-[12px] uppercase tracking-widest opacity-50 mb-10">Powering sales teams at</p>
                <div className="flex flex-wrap justify-center gap-12 opacity-40 grayscale hover:grayscale-0 hover:opacity-80 transition-all">
                    {["SALESFORCE", "HUBSPOT", "OUTREACH", "APOLLO", "LEMLIST"].map(logo => (
                        <div key={logo} className="text-lg font-black">{logo}</div>
                    ))}
                </div>
            </section>

            {/* Intelligence Carousel Section */}
            <IntelligenceCarousel />

            {/* The Requested Pop-up Component integration */}
            <CTASection
                isPopup={true}
                title="Ready to bypass the gatekeeper?"
                description="Join LeadSnipe today and start reaching decision-makers who actually sign checks."
                action={{
                    text: "Claim Your Account",
                    href: "/login",
                    variant: "glow"
                }}
                badge={{ text: "Limited Access" }}
            />

            {/* Footer Mobile Fix */}
            <div className="md:hidden fixed bottom-0 left-0 w-full bg-[#0D0D14] p-4 flex justify-between items-center z-[1000] border-t border-white/10">
                <div className="flex flex-col text-white">
                    <span className="font-bold text-sm">Find 50 Leads</span>
                    <span className="text-[10px] opacity-60 font-sans">Starts for Free</span>
                </div>
                <Button className="bg-[#7C3AED] hover:bg-[#8B5CF6]">Get Started</Button>
            </div>

            {/* FOMO Toast */}
            {toastVisible && (
                <div className="fixed bottom-24 left-6 bg-white p-4 rounded-xl shadow-2xl border border-black/5 flex items-center gap-3 animate-in fade-in slide-in-from-left-8 duration-500 z-[900]">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-[0_0_10px_#22c55e]" />
                    <span className="text-xs font-medium">{toastText}</span>
                </div>
            )}

            <style jsx global>{`
        @keyframes float {
          0%, 100% { transform: translateY(0) rotate(0deg); }
          50% { transform: translateY(-20px) rotate(1deg); }
        }
        @keyframes float-delay {
          0%, 100% { transform: translateY(0) rotate(0deg); }
          50% { transform: translateY(-15px) rotate(-1deg); }
        }
        .animate-float { animation: float 8s ease-in-out infinite; }
        .animate-float-delay { animation: float-delay 7s ease-in-out infinite; }
        
        .kinetic-text {
          opacity: 0;
          transform: translateY(20px);
          animation: text-reveal 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        @keyframes text-reveal {
          to { transform: translateY(0); opacity: 1; }
        }
        
        .font-serif { font-family: 'Instrument Serif', serif; }
        .font-sans { font-family: 'Inter', sans-serif; }
      `}</style>
        </div>
    )
}
