"use client"

import * as React from "react"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { X } from "lucide-react"

interface CTAProps {
    badge?: {
        text: string
    }
    title: string
    description?: string
    action: {
        text: string
        href: string
        variant?: "default" | "glow"
    }
    withGlow?: boolean
    className?: string
    isPopup?: boolean
}

export function CTASection({
    badge,
    title,
    description,
    action,
    withGlow = true,
    className,
    isPopup = false,
}: CTAProps) {
    const [isVisible, setIsVisible] = useState(false)

    useEffect(() => {
        if (isPopup) {
            const timer = setTimeout(() => setIsVisible(true), 1500) // Delay for pop-up effect
            return () => clearTimeout(timer)
        } else {
            setIsVisible(true)
        }
    }, [isPopup])

    if (!isVisible) return null

    const content = (
        <div className={cn("relative mx-auto flex max-w-container flex-col items-center gap-6 px-8 py-12 text-center sm:gap-8 md:py-24", isPopup && "bg-background/95 backdrop-blur-sm border rounded-3xl shadow-2xl")}>
            {isPopup && (
                <button
                    onClick={() => setIsVisible(false)}
                    className="absolute right-4 top-4 p-2 hover:bg-muted rounded-full transition-colors"
                >
                    <X className="w-5 h-5" />
                </button>
            )}

            {/* Badge */}
            {badge && (
                <Badge
                    variant="outline"
                    className="opacity-0 animate-fade-in-up delay-100"
                >
                    <span className="text-muted-foreground">{badge.text}</span>
                </Badge>
            )}

            {/* Title */}
            <h2 className="text-3xl font-semibold sm:text-5xl opacity-0 animate-fade-in-up delay-200">
                {title}
            </h2>

            {/* Description */}
            {description && (
                <p className="text-muted-foreground opacity-0 animate-fade-in-up delay-300">
                    {description}
                </p>
            )}

            {/* Action Button */}
            <Button
                variant={action.variant || "default"}
                size="lg"
                className="opacity-0 animate-fade-in-up delay-500"
                asChild
            >
                <a href={action.href}>{action.text}</a>
            </Button>

            {/* Glow Effect */}
            {withGlow && (
                <div className="fade-top-lg pointer-events-none absolute inset-0 rounded-2xl shadow-glow opacity-0 animate-scale-in delay-700" />
            )}
        </div>
    )

    if (isPopup) {
        return (
            <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/20 animate-in fade-in duration-500">
                <section className={cn("overflow-hidden w-full max-w-4xl animate-in zoom-in-95 duration-500", className)}>
                    {content}
                </section>
            </div>
        )
    }

    return (
        <section className={cn("overflow-hidden pt-0 md:pt-0", className)}>
            {content}
        </section>
    )
}
