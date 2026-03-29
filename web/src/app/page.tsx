import type { Metadata } from "next";
import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";
import Landing from "@/components/landing";

export const metadata: Metadata = {
  title: "StewardMe - Know what matters next",
  description:
    "StewardMe turns your notes, goals, and live signals into a clear next step.",
  openGraph: {
    title: "StewardMe - Know what matters next",
    description:
      "StewardMe turns your notes, goals, and live signals into a clear next step.",
    url: "https://stewardme.ai",
    siteName: "StewardMe",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "StewardMe - Know what matters next",
    description:
      "StewardMe turns your notes, goals, and live signals into a clear next step.",
  },
};

export default async function RootPage() {
  const session = await auth();
  if (session?.user) {
    redirect("/home");
  }
  return <Landing />;
}
