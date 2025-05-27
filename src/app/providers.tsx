// src/app/providers.tsx
'use client'; // This must be a Client Component

import { WagmiProvider } from 'wagmi';
import { wagmiConfig } from '@/wagmi.config'; // Assuming your wagmi config is in src/
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

// Create a react-query client
const queryClient = new QueryClient();

export function Providers({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = React.useState(false);
  React.useEffect(() => setMounted(true), []); // Ensure component is mounted before rendering Wagmi parts to avoid hydration issues

  return (
    <WagmiProvider config={wagmiConfig}>
      <QueryClientProvider client={queryClient}>
        {mounted && children}
      </QueryClientProvider>
    </WagmiProvider>
  );
}
