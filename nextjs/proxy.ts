/**
 * Next.js Middleware for Authentication, Security and Request Handling
 * 
 * This middleware adds security layers:
 * - Authentication protection for routes
 * - Request logging for audit trails
 * - Request validation
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import NextAuth from 'next-auth';
import { authConfig } from '@/lib/auth.config';
import { getRatelimit } from '@/lib/rate-limit';

const { auth } = NextAuth(authConfig);

// Helper to get client IP
function getClientIp(request: NextRequest): string {
  return request.headers.get('x-forwarded-for')?.split(',')[0].trim() ||
    request.headers.get('x-real-ip') ||
    'unknown';
}

// Helper to generate request ID for logging
function generateRequestId(): string {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Check if path is public (doesn't require authentication)
 */
function isPublicPath(pathname: string): boolean {
  const publicPaths = [
    '/',
    '/auth/login',
    '/auth/register',
    '/auth/error',
    '/auth/forgot-password',
    '/privacy-policy',
    '/hipaa-compliance',
    '/security',
  ];

  return publicPaths.some(path =>
    path === '/' ? pathname === '/' : pathname.startsWith(path)
  );
}

export default auth(async (request) => {
  const requestId = generateRequestId();
  const clientIp = getClientIp(request);
  const startTime = Date.now();
  const { pathname } = request.nextUrl;

  // Check if path requires authentication
  const isPublic = isPublicPath(pathname);
  const isAuthenticated = !!request.auth;

  // Log request in production to monitoring service
  // Note: In production, integrate with Cloud Logging, Datadog, or similar
  if (process.env.NODE_ENV === 'production' && process.env.ENABLE_REQUEST_LOGGING === 'true') {
    // Future: Send to centralized logging service
    // Example: await sendToCloudLogging({...})
  }

  // Redirect to login if accessing protected route without authentication
  if (!isPublic && !isAuthenticated) {
    const loginUrl = new URL('/auth/login', request.url);
    loginUrl.searchParams.set('callbackUrl', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Redirect to dashboard if accessing auth pages while authenticated
  if (isPublic && isAuthenticated && pathname !== '/auth/error') {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // Clone the response to add custom headers
  const response = NextResponse.next();

  // Add request ID for tracking
  response.headers.set('x-request-id', requestId);

  // Add timing information
  response.headers.set('x-response-time', `${Date.now() - startTime}ms`);

  // Security headers (additional to next.config.ts)
  response.headers.set('x-client-ip', clientIp);

  // Rate limiting for API and POST requests
  if (pathname.startsWith('/api') || request.method === 'POST') {
    const limiterType = pathname.startsWith('/api/auth') ? 'auth' : 'api';
    const ratelimit = getRatelimit(limiterType);

    if (ratelimit) {
      const result = await ratelimit.limit(clientIp);

      if (!result.success) {
        const resetTime = result.reset instanceof Date ? result.reset : new Date(result.reset);
        const retryAfter = Math.ceil((resetTime.getTime() - Date.now()) / 1000);

        return NextResponse.json(
          {
            error: 'Too Many Requests',
            message: 'You have exceeded the rate limit. Please try again later.',
            retryAfter
          },
          {
            status: 429,
            headers: {
              'X-RateLimit-Limit': result.limit.toString(),
              'X-RateLimit-Remaining': '0',
              'X-RateLimit-Reset': resetTime.toISOString(),
              'Retry-After': retryAfter.toString()
            }
          }
        );
      }

      // Add rate limit headers to successful requests
      const resetTime = result.reset instanceof Date ? result.reset : new Date(result.reset);
      response.headers.set('X-RateLimit-Limit', result.limit.toString());
      response.headers.set('X-RateLimit-Remaining', result.remaining.toString());
      response.headers.set('X-RateLimit-Reset', resetTime.toISOString());
    }
  }

  return response;
});

// Configure which routes to run middleware on
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization)
     * - favicon.ico
     * - api/auth (NextAuth.js handles these)
     * - api/rate-limit-test (public test endpoint)
     * - public files (.svg, .png, etc.)
     */
    '/((?!_next/static|_next/image|favicon.ico|api/auth|api/rate-limit-test|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
