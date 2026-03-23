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
  description: "AI tutor and steward that teaches what matters, tracks your learning, and scans the world so you know what's next",
  metadataBase: new URL("https://stewardme.ai"),
  openGraph: {
    title: "StewardMe",
    description: "AI tutor and steward that teaches what matters, tracks your learning, and scans the world so you know what's next",
    url: "https://stewardme.ai",
    siteName: "StewardMe",
    images: [{ url: "/og-image.jpg", width: 1024, height: 1024 }],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "StewardMe",
    description: "AI tutor and steward that teaches what matters, tracks your learning, and scans the world so you know what's next",
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
