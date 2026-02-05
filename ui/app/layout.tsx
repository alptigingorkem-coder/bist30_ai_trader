import Sidebar from "@/components/layout/Sidebar";
import HealthMonitor from "@/components/layout/HealthMonitor";
import { Geist, Geist_Mono } from "next/font/google";
import "@/app/globals.css";
import AlertToast from "@/components/alerts/AlertToast";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "BIST30 AI TRADER DASHBOARD",
  description: "Next.js AI Trader Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <body
        className={`${geistMono.className} bg-[var(--color-dash-bg)] text-[var(--color-dash-text)] antialiased`}
      >
        <div className="flex flex-row h-screen overflow-hidden">
          <Sidebar />
          <div className="flex-1 flex flex-col h-full bg-[var(--color-dash-bg)] relative">
            {/* Header / Top Bar for Health Monitor */}
            <div className="absolute top-6 right-8 z-50">
              <HealthMonitor />
            </div>

            <main className="flex-1 overflow-y-auto p-6 md:p-8 scrollbar-hide">
              {children}
            </main>
          </div>
        </div>
        {/* Global Alert Toasts */}
        <AlertToast />
      </body>
    </html>
  );
}
