import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
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
  title: "Lumina App Store",
  description: "Marketplace cho addon trong hệ sinh thái Lumina",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="vi"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-gray-50 dark:bg-[#111111]">
        <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-3 flex items-center gap-4">
          <a href="/" className="text-xl font-bold text-gray-900 dark:text-white">
            Lumina App Store
          </a>
          <nav className="flex gap-4 ml-8 text-sm">
            <a href="/" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">Marketplace</a>
            <a href="/authoring" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">Authoring</a>
            <a href="/menu-apps" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">Menu Apps</a>
          </nav>
        </header>
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
