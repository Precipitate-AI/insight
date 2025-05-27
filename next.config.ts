/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    ALCHEMY_KEY: process.env.ALCHEMY_KEY,
     // We will add OPENROUTER_API_KEY here later if accessed by frontend
     // For now, it's mainly for the backend Python script
  },
};

module.exports = nextConfig;
