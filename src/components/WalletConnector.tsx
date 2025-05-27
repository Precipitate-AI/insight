// src/components/WalletConnector.tsx
'use client';
import { useAccount, useConnect, useDisconnect } from 'wagmi';
// import { injected } from 'wagmi/connectors'; // << See note below
import { useConnectors } from 'wagmi'; // Better way to get connectors
import { useEffect, useState } from 'react';

export default function WalletConnector() { // <<--- Change this back
  const { connect } = useConnect();
  const { disconnect } = useDisconnect();
  const { address } = useAccount();
  const [mounted, setMounted] = useState(false);
  const connectors = useConnectors(); // Get all configured connectors
  const injectedConnector = connectors.find(c => c.type === 'injected');


  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return address ? (
    <button
      onClick={() => disconnect()}
      className="px-4 py-2 bg-precipitate-blue text-white rounded-lg hover:bg-blue-600 transition-colors"
    >
      {address.slice(0, 6)}...{address.slice(-4)}
    </button>
  ) : (
    <button
      onClick={() => {
        if (injectedConnector) {
          connect({ connector: injectedConnector });
        } else {
          // Handle case where no injected connector is found,
          // maybe prompt user to install MetaMask or open a WalletConnect modal if configured
          alert("No injected wallet (like MetaMask) found. Please install one.");
        }
      }}
      disabled={!injectedConnector} // Disable if no injected connector
      className="px-4 py-2 bg-precipitate-blue text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-60"
    >
      {injectedConnector ? 'Connect Wallet' : 'No Wallet Detected'}
    </button>
  );
}
