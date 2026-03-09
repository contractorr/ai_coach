import type { Metadata } from "next";
import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";
import Landing from "@/components/landing";

export const metadata: Metadata = {
  title: "StewardMe — Know what matters next",
  description:
    "Open-source AI steward that scans HN, GitHub, arXiv, Reddit & RSS, learns from your journal, and tells you what matters next.",
  openGraph: {
    title: "StewardMe — Know what matters next",
    description:
      "Open-source AI steward that scans HN, GitHub, arXiv, Reddit & RSS, learns from your journal, and tells you what matters next.",
    url: "https://stewardme.ai",
    siteName: "StewardMe",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "StewardMe — Know what matters next",
    description:
      "Open-source AI steward that scans HN, GitHub, arXiv, Reddit & RSS, learns from your journal, and tells you what matters next.",
  },
};

export default async function RootPage() {
  const session = await auth();
  if (session?.user) {
    redirect("/home");
  }
  return <Landing />;
}
