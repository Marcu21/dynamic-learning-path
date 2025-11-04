/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  eslint: {
    // Disable ESLint during builds to avoid blocking issues
    ignoreDuringBuilds: false,
  },
  typescript: {
    // Disable TypeScript errors during builds (warnings only)
    ignoreBuildErrors: false,
  },
};

module.exports = nextConfig;