import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin", "vietnamese"] });

export const metadata: Metadata = {
  title: "MyTravel - AI-Powered Vietnam Travel Planner",
  description: "Plan your perfect Vietnam trip with AI assistance. Discover accommodations, restaurants, transportation, and activities across Vietnam.",
  keywords: ["Vietnam", "travel", "AI", "trip planner", "accommodation", "restaurants", "itinerary"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
