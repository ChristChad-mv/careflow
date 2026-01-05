import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  /* config options here */

  // Turbopack configuration
  turbopack: {
    root: '/home/audrey/Bureau/careflow/nextjs',
  },

  // Security headers for production
  async headers() {
    return [
      {
        // Apply security headers to all routes
        source: '/(.*)',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=(), interest-cohort=()'
          },
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              // Script Src: Allow self, unsafe-eval (Next.js dev), unsafe-inline (Next.js hydration)
              "script-src 'self' 'unsafe-eval' 'unsafe-inline' https://apis.google.com",
              // Style Src: Allow self, unsafe-inline (CSS-in-JS), Google Fonts
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              // Font Src: Self + Google Fonts
              "font-src 'self' https://fonts.gstatic.com",
              // Img Src: Self + Data URIs + HTTPS (for avatars)
              "img-src 'self' data: https:",
              // Connect Src: Critical for Firebase, Vercel, Google APIs
              "connect-src 'self' https://vercel.live https://identitytoolkit.googleapis.com https://securetoken.googleapis.com https://firestore.googleapis.com https://www.googleapis.com https://*.firebaseapp.com https://apis.google.com",
              "frame-ancestors 'self'",
              "base-uri 'self'",
              "form-action 'self'"
            ].join('; ')
          }
        ],
      },
    ];
  },

  // Disable X-Powered-By header
  poweredByHeader: false,

  // Enable React strict mode for better error catching
  reactStrictMode: true,

  // Compress responses
  compress: true,

  // Optimize images
  images: {
    domains: [],
    formats: ['image/avif', 'image/webp'],
  },
};

export default nextConfig;
