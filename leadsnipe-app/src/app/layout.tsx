import type { Metadata, Viewport } from "next";
import { Sora, DM_Sans, JetBrains_Mono } from 'next/font/google';
import "./globals.css";
import { Header } from "@/components/Header";
import { Sidebar } from "@/components/Sidebar";

const sora = Sora({
  subsets: ['latin'],
  variable: '--font-display',
  display: 'swap',
});

const dmSans = DM_Sans({
  subsets: ['latin'],
  variable: '--font-body',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
});

export const metadata: Metadata = {
  title: "LeadSnipe | B2B Lead Generation Platform",
  description: "Find decision makers, emails, and LinkedIn profiles for B2B outreach campaigns in seconds.",
  keywords: ["lead generation", "B2B", "sales", "email finder", "decision maker", "LinkedIn"],
  authors: [{ name: "LeadSnipe" }],
  openGraph: {
    title: "LeadSnipe | B2B Lead Generation Platform",
    description: "Find decision makers, emails, and LinkedIn profiles for B2B outreach campaigns in seconds.",
    type: "website",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#FFFFFF",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${sora.variable} ${dmSans.variable} ${jetbrainsMono.variable}`}>
      <body className="min-h-screen bg-[var(--color-bg-secondary)] antialiased">
        {/* Sidebar */}
        <Sidebar />

        {/* Main content area */}
        <div className="pl-64 flex flex-col min-h-screen">
          {/* Header */}
          <Header />

          {/* Main content */}
          <main className="flex-1 p-12 pt-0">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
