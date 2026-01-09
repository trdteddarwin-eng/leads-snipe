import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
    title: "LeadSnipe | Sentient Lead Intelligence",
    description: "Bypass generic filters and talk to decision makers directly.",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <body className="antialiased">
                {children}
            </body>
        </html>
    );
}
