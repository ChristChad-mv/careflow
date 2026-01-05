/**
 * CSRF Token Management
 * 
 * Custom CSRF protection for API routes that need additional protection
 * beyond NextAuth's built-in cookie-based protection.
 * 
 * Usage in API routes:
 * ```typescript
 * import { validateCsrfToken, generateCsrfToken } from '@/lib/csrf';
 * 
 * // Generate token (e.g., in a GET endpoint)
 * const token = await generateCsrfToken(request);
 * 
 * // Validate token (e.g., in POST/PUT/DELETE endpoints)
 * const isValid = await validateCsrfToken(request);
 * if (!isValid) {
 *   return NextResponse.json({ error: 'Invalid CSRF token' }, { status: 403 });
 * }
 * ```
 */

import { headers } from 'next/headers';
import { NextRequest } from 'next/server';

// CSRF configuration
const CSRF_HEADER = 'x-csrf-token';
const CSRF_COOKIE = 'csrf-token';

/**
 * Generate a CSRF token for the current session
 */
export async function generateCsrfToken(request: NextRequest): Promise<string> {
  const headersList = await headers();
  const userAgent = headersList.get('user-agent') || '';
  const sessionId = request.cookies.get('next-auth.session-token')?.value || 
                     request.cookies.get('__Secure-next-auth.session-token')?.value ||
                     'anonymous';
  
  // Create a simple token based on session + secret
  // In production, consider using a more robust token generation
  const tokenData = `${sessionId}-${userAgent}-${Date.now()}`;
  const token = Buffer.from(tokenData).toString('base64url');
  
  return token;
}

/**
 * Validate CSRF token from request headers
 */
export async function validateCsrfToken(request: NextRequest): Promise<boolean> {
  // Skip CSRF validation for safe methods
  const method = request.method.toUpperCase();
  if (['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    return true;
  }

  // Get token from header
  const headerToken = request.headers.get(CSRF_HEADER);
  
  // Get token from cookie
  const cookieToken = request.cookies.get(CSRF_COOKIE)?.value;

  // Both must exist and match
  if (!headerToken || !cookieToken) {
    console.warn('CSRF validation failed: Missing token');
    return false;
  }

  if (headerToken !== cookieToken) {
    console.warn('CSRF validation failed: Token mismatch');
    return false;
  }

  return true;
}

/**
 * Middleware helper to check CSRF token
 * Returns true if valid, false otherwise
 */
export function checkCsrfToken(request: NextRequest): boolean {
  const method = request.method.toUpperCase();
  
  // Skip for safe methods
  if (['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    return true;
  }

  const headerToken = request.headers.get(CSRF_HEADER);
  const cookieToken = request.cookies.get(CSRF_COOKIE)?.value;

  return !!(headerToken && cookieToken && headerToken === cookieToken);
}

/**
 * Response headers to set CSRF token cookie
 */
export function getCsrfCookieHeader(token: string): string {
  const secure = process.env.NODE_ENV === 'production';
  const sameSite = 'lax';
  
  return `${CSRF_COOKIE}=${token}; Path=/; HttpOnly; SameSite=${sameSite}${secure ? '; Secure' : ''}; Max-Age=86400`;
}
