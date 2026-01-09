import { CTASection } from "@/components/ui/cta-with-rectangle"

export function CTADemo() {
    return (
        <div className="space-y-24 py-12">
            {/* Standard Section usage */}
            <CTASection
                badge={{ text: "Get started" }}
                title="Start building with Launch UI"
                description="Get started with Launch UI and build your landing page in no time"
                action={{
                    text: "Get Started Now",
                    href: "/docs",
                    variant: "default"
                }}
                isPopup={false}
            />

            {/* The 'Cool Pop-up' version requested (renders as overlay) */}
            <CTASection
                badge={{ text: "Special Offer" }}
                title="Exclusive Early Access"
                description="Join the waitlist today and get 50% off your first month of LeadSnipe Pro."
                action={{
                    text: "Claim Your Discount",
                    href: "/login",
                    variant: "glow"
                }}
                isPopup={true}
            />
        </div>
    )
}
