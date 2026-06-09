import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "EcoTrace AI+ — Intelligent Carbon Footprint Tracker",
    template: "%s | EcoTrace AI+",
  },
  description:
    "Track and reduce your carbon footprint with Explainable AI (SHAP), Digital Carbon Twin forecasting, OCR receipt intelligence, and community gamification.",
  keywords: [
    "carbon footprint",
    "sustainability",
    "explainable AI",
    "SHAP",
    "digital twin",
    "climate action",
  ],
  authors: [{ name: "EcoTrace AI+" }],
  openGraph: {
    title: "EcoTrace AI+ — Intelligent Carbon Footprint Tracker",
    description:
      "From Awareness to Action. The intelligent carbon tracking platform powered by Explainable AI and Digital Twins.",
    type: "website",
    locale: "en_US",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
