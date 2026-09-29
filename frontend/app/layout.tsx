import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { TransitionProvider } from "@/components/ui/TransitionProvider";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: {
    default: "E-Commerce Smart Review & Sentiment Engine",
    template: "%s | Sentiment Engine",
  },
  description:
    "Transform customer feedback into explainable product intelligence.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-sans`}>
        <TransitionProvider>{children}</TransitionProvider>
      </body>
    </html>
  );
}
