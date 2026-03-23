import type { Metadata } from "next";
import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";
import Landing from "@/components/landing";

export const metadata: Metadata = {
  title: "StewardMe — Your AI tutor and steward",
  description:
    "Open-source AI tutor that teaches what matters with spaced repetition, scans HN, GitHub, arXiv & RSS, and gives personalized guidance grounded in your journal.",
  openGraph: {
    title: "StewardMe — Your AI tutor and steward",
    description:
      "Open-source AI tutor that teaches what matters with spaced repetition, scans HN, GitHub, arXiv & RSS, and gives personalized guidance grounded in your journal.",
    url: "https://stewardme.ai",
    siteName: "StewardMe",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "StewardMe — Your AI tutor and steward",
    description:
      "Open-source AI tutor that teaches what matters with spaced repetition, scans HN, GitHub, arXiv & RSS, and gives personalized guidance grounded in your journal.",
  },
};

export default async function RootPage() {
  const session = await auth();
  if (session?.user) {
    redirect("/home");
  }
  return <Landing />;
}
