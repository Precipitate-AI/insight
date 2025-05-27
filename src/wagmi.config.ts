// src/wagmi.config.ts
import { createConfig, http } from 'wagmi';
import { mainnet, base, arbitrum, optimism, polygon } from 'wagmi/chains'; // Added a few more common chains

// Ensure your Alchemy key is correctly exposed as NEXT_PUBLIC_ALCHEMY_KEY in your .env.local
const alchemyApiKey = process.env.NEXT_PUBLIC_ALCHEMY_KEY;

if (!alchemyApiKey) {
  console.warn(
    'WAGMI_CONFIG: NEXT_PUBLIC_ALCHEMY_KEY is not set. Vercel deployments will fail if this is required for build-time SSR. For local dev, RPC calls might fail.'
  );
  // You might choose to throw an error here if Alchemy is strictly required at build/runtime
  // For now, we'll allow it to proceed so local dev can sometimes work with default public RPCs if wagmi falls back.
}

export const wagmiConfig = createConfig({
  chains: [mainnet, base, arbitrum, optimism, polygon], // Add or remove chains as needed
  multiInjectedProviderDiscovery: true, // Helps discover multiple EIP-6963 providers (e.g., multiple browser wallets)
  transports: {
    [mainnet.id]: http(
      alchemyApiKey ? `https://eth-mainnet.g.alchemy.com/v2/${alchemyApiKey}` : 'https://cloudflare-eth.com' // Fallback to public RPC
    ),
    [base.id]: http(
      alchemyApiKey ? `https://base-mainnet.g.alchemy.com/v2/${alchemyApiKey}` : 'https://mainnet.base.org' // Fallback to public RPC
    ),
    [arbitrum.id]: http(
      alchemyApiKey ? `https://arb-mainnet.g.alchemy.com/v2/${alchemyApiKey}` : 'https://arb1.arbitrum.io/rpc' // Fallback
    ),
    [optimism.id]: http(
      alchemyApiKey ? `https://opt-mainnet.g.alchemy.com/v2/${alchemyApiKey}` : 'https://mainnet.optimism.io' // Fallback
    ),
    [polygon.id]: http(
      alchemyApiKey ? `https://polygon-mainnet.g.alchemy.com/v2/${alchemyApiKey}` : 'https://polygon-rpc.com' // Fallback
    ),
  },
  ssr: true, // Enable SSR for Wagmi, helps with initial state hydration
});
