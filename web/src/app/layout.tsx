import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Toaster } from "sonner";
import { SessionProvider } from "@/components/SessionProvider";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "StewardMe",
  description: "Your personal intelligence steward for focus, monitoring, learning, and reflection.",
  metadataBase: new URL("https://stewardme.ai"),
  openGraph: {
    title: "StewardMe",
    description: "Your personal intelligence steward for focus, monitoring, learning, and reflection.",
    url: "https://stewardme.ai",
    siteName: "StewardMe",
    images: [{ url: "/og-image.jpg", width: 1024, height: 1024 }],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "StewardMe",
    description: "Your personal intelligence steward for focus, monitoring, learning, and reflection.",
    images: ["/og-image.jpg"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <SessionProvider>
          {children}
          <Toaster />
        </SessionProvider>
      </body>
    </html>
  );
}
