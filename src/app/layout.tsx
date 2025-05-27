// src/app/layout.tsx
import './globals.css';
import type { Metadata } from 'next';
import { Providers } from './providers'; // <--- Import Providers

export const metadata: Metadata = {
  title: 'Insight - Hyperliquid Summaries',
  description: 'AI-powered summaries of Hyperliquid trading activity.',
  icons: {
    icon: '/favicon.png',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      </head>
      <body className="min-h-screen"> {/* precipitate-dark should be applied via globals.css */}
        <Providers>{children}</Providers> {/* <--- Wrap children with Providers */}
      </body>
    </html>
  );
}
