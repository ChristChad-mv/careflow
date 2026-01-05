import { NextRequest, NextResponse } from 'next/server';
import { generateCsrfToken, getCsrfCookieHeader } from '@/lib/csrf';

/**
 * CSRF Token Endpoint
 * 
 * GET /api/csrf - Generate and return a CSRF token
 * 
 * This endpoint generates a CSRF token and sets it as a cookie.
 * Frontend should call this on app load and include the token
 * in the X-CSRF-Token header for state-changing requests.
 */
export async function GET(request: NextRequest) {
  try {
    // Generate CSRF token
    const token = await generateCsrfToken(request);

    // Create response with token
    const response = NextResponse.json({
      token,
      message: 'CSRF token generated successfully',
    });

    // Set cookie
    response.headers.set('Set-Cookie', getCsrfCookieHeader(token));

    return response;
  } catch (error) {
    console.error('CSRF token generation error:', error);
    return NextResponse.json(
      { error: 'Failed to generate CSRF token' },
      { status: 500 }
    );
  }
}
