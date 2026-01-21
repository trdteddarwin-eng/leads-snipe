"use client"

import * as React from "react"
import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import { ChevronLeft, ChevronRight } from "lucide-react"

interface Feature {
    id: number
    title: string
    subtitle: string
    description: string
    icon: React.ReactNode
    visual: React.ReactNode
}

const features: Feature[] = [
    {
        id: 1,
        title: "Neural Scraping",
        subtitle: "Real-time Discovery",
        description: "Our bots simulate human browsing to extract deep data from local directories without getting blocked.",
        icon: <span>🎯</span>,
        visual: (
            <div className="absolute inset-0 flex items-center justify-center opacity-20">
                <div className="w-64 h-64 border-[0.5px] border-black/10 rounded-full animate-ping" />
                <div className="absolute w-48 h-48 border-[0.5px] border-black/10 rounded-full animate-pulse" />
                <div className="grid grid-cols-4 gap-2 opacity-30">
                    {[...Array(16)].map((_, i) => (
                        <div key={i} className="w-8 h-8 bg-[#7C3AED]/20 rounded-sm" />
                    ))}
                </div>
            </div>
        )
    },
    {
        id: 2,
        title: "Decision-Maker ID",
        subtitle: "AI Lead Enrichment",
        description: "Go beyond generic info@ emails. We correlate LinkedIn, Twitter, and domain data to find the CEO.",
        icon: <span>👤</span>,
        visual: (
            <div className="absolute inset-0 flex items-center justify-center">
                <div className="relative">
                    <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#7C3AED] to-[#3B82F6] opacity-10 animate-pulse" />
                    <div className="absolute top-0 left-0 w-full h-full flex items-center justify-center">
                        <div className="w-2 h-2 bg-[#7C3AED] rounded-full animate-bounce" />
                    </div>
                </div>
                <div className="absolute grid grid-cols-2 gap-20">
                    <div className="w-10 h-1 bg-black/5 rotate-45" />
                    <div className="w-10 h-1 bg-black/5 -rotate-45" />
                </div>
            </div>
        )
    },
    {
        id: 3,
        title: "Sentient Outreach",
        subtitle: "Psychological Hooks",
        description: "Our LLMs analyze lead websites to generate custom opening lines that sound 100% human.",
        icon: <span>✍️</span>,
        visual: (
            <div className="absolute inset-0 p-8 flex flex-col gap-4 opacity-10">
                <div className="h-4 w-3/4 bg-black/20 rounded-full" />
                <div className="h-4 w-1/2 bg-black/20 rounded-full" />
                <div className="h-4 w-full bg-black/20 rounded-full" />
                <div className="mt-4 h-4 w-1/4 bg-[#7C3AED] rounded-full" />
            </div>
        )
    }
]

export function IntelligenceCarousel() {
    const [index, setIndex] = useState(0)

    const next = () => setIndex((prev) => (prev + 1) % features.length)
    const prev = () => setIndex((prev) => (prev - 1 + features.length) % features.length)

    return (
        <section className="py-24 overflow-hidden bg-[#F5F5F4] relative">
            <div className="max-w-7xl mx-auto px-[5%] mb-16 text-center">
                <span className="text-[10px] font-bold tracking-[0.2em] uppercase text-[#7C3AED] block mb-4">How it works</span>
                <h2 className="text-4xl md:text-6xl font-serif">A Sentient Discovery Engine</h2>
            </div>

            <div className="relative flex items-center justify-center h-[500px] w-full max-w-5xl mx-auto">
                {/* Navigation Buttons */}
                <button onClick={prev} className="absolute left-4 z-50 p-4 bg-white rounded-full shadow-lg hover:scale-110 transition-transform hidden md:block">
                    <ChevronLeft className="w-6 h-6" />
                </button>
                <button onClick={next} className="absolute right-4 z-50 p-4 bg-white rounded-full shadow-lg hover:scale-110 transition-transform hidden md:block">
                    <ChevronRight className="w-6 h-6" />
                </button>

                <div className="relative w-full h-full flex items-center justify-center perspective-[1000px]">
                    <AnimatePresence initial={false}>
                        {[-1, 0, 1].map((offset) => {
                            const currentIdx = (index + offset + features.length) % features.length
                            const feature = features[currentIdx]

                            const isCenter = offset === 0

                            return (
                                <motion.div
                                    key={`${currentIdx}-${offset}`}
                                    initial={{ opacity: 0, x: offset * 300, scale: 0.8 }}
                                    animate={{
                                        opacity: isCenter ? 1 : 0.4,
                                        x: offset * (isCenter ? 0 : 400),
                                        scale: isCenter ? 1 : 0.8,
                                        zIndex: isCenter ? 10 : 0
                                    }}
                                    exit={{ opacity: 0, x: -offset * 300, scale: 0.8 }}
                                    transition={{ type: "spring", stiffness: 300, damping: 300 }}
                                    className={cn(
                                        "absolute w-full max-w-[400px] aspect-[4/5] bg-white rounded-[32px] p-10 shadow-2xl border border-black/5 overflow-hidden flex flex-col justify-between cursor-pointer",
                                        !isCenter && "pointer-events-none"
                                    )}
                                    onClick={() => !isCenter && setIndex(currentIdx)}
                                >
                                    {/* Background Visual */}
                                    {feature.visual}

                                    <div className="relative z-10">
                                        <div className="text-4xl mb-6">{feature.icon}</div>
                                        <div className="text-[10px] font-bold tracking-widest text-[#7C3AED] uppercase mb-2">{feature.subtitle}</div>
                                        <h3 className="text-3xl font-bold mb-4">{feature.title}</h3>
                                    </div>

                                    <div className="relative z-10">
                                        <p className="text-[#0D0D14]/60 leading-relaxed text-lg">{feature.description}</p>
                                    </div>
                                </motion.div>
                            )
                        })}
                    </AnimatePresence>
                </div>
            </div>

            {/* Pagination Dots */}
            <div className="flex justify-center gap-2 mt-12">
                {features.map((_, i) => (
                    <div
                        key={i}
                        className={cn(
                            "w-2 h-2 rounded-full transition-all duration-300",
                            index === i ? "w-8 bg-[#7C3AED]" : "bg-black/10"
                        )}
                    />
                ))}
            </div>
        </section>
    )
}
