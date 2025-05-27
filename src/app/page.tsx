// src/app/page.tsx
'use client'; // Needs to be client component if it uses hooks or event handlers directly

import Image from 'next/image';
import WalletConnector from '@/components/WalletConnector'; // <--- Import

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-precipitate-dark text-precipitate-light">
      <header className="fixed top-0 left-0 right-0 p-4 md:p-6 flex justify-between items-center z-50 bg-precipitate-dark/80 backdrop-blur-md">
        <Image
          src="/logo.png"
          width={50}
          height={71}
          alt="Precipitate AI Insight"
          priority
          className="w-[40px] h-auto md:w-[50px]"
        />
        <WalletConnector /> {/* <--- Add WalletConnector here */}
      </header>

      <main className="text-center pt-24 pb-12 px-4"> {/* Added padding-top to avoid overlap with fixed header */}
        <h1 className="text-4xl sm:text-5xl font-bold mb-4">
          Insight
        </h1>
        <p className="text-lg sm:text-xl text-gray-400 mb-8 max-w-xl mx-auto">
          AI-Powered Hyperliquid Trading Summaries & Analytics
        </p>
        <div className="p-6 bg-precipitate-light bg-opacity-5 backdrop-blur-sm border border-precipitate-light/20 rounded-lg shadow-xl">
          <p className="text-gray-300">Trading report data will be displayed here.</p>
          <p className="text-sm text-gray-500 mt-4">
            Connect your wallet to potentially unlock personalized features in the future.
          </p>
        </div>
      </main>

      <footer className="fixed bottom-0 left-0 right-0 p-3 md:p-4 text-center text-xs md:text-sm text-gray-500 bg-precipitate-dark/80 backdrop-blur-md">
        Powered by Precipitate AI
      </footer>
    </div>
  );
}
