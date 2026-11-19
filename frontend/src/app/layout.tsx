import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "VoiceBridge AI — Real-Time Co-Pilot & Web Studio",
  description: "Next.js Accessibility Web Studio, Teleprompter & Live Interview Co-Pilot",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${jetbrainsMono.variable} antialiased selection:bg-blue-500/20 selection:text-blue-500`}>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
