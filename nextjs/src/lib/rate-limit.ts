/**
 * Rate Limiting Configuration
 * 
 * Production-ready rate limiting using Upstash Redis.
 * Falls back to in-memory limiting for development.
 */

import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

// Check if Redis credentials are configured
const isRedisConfigured = 
  process.env.UPSTASH_REDIS_REST_URL && 
  process.env.UPSTASH_REDIS_REST_TOKEN;

// Initialize Redis client (only in production with credentials)
const redis = isRedisConfigured
  ? new Redis({
      url: process.env.UPSTASH_REDIS_REST_URL!,
      token: process.env.UPSTASH_REDIS_REST_TOKEN!,
    })
  : undefined;

// Rate limit configurations for different routes
export const apiRatelimit = redis
  ? new Ratelimit({
      redis,
      limiter: Ratelimit.slidingWindow(20, '1 m'), // 20 requests per minute
      analytics: true,
      prefix: 'ratelimit:api',
    })
  : null;

export const authRatelimit = redis
  ? new Ratelimit({
      redis,
      limiter: Ratelimit.slidingWindow(5, '5 m'), // 5 login attempts per 5 minutes
      analytics: true,
      prefix: 'ratelimit:auth',
    })
  : null;

export const generalRatelimit = redis
  ? new Ratelimit({
      redis,
      limiter: Ratelimit.slidingWindow(100, '1 m'), // 100 requests per minute
      analytics: true,
      prefix: 'ratelimit:general',
    })
  : null;

// In-memory rate limiting fallback for development
class InMemoryRatelimit {
  private requests = new Map<string, number[]>();
  private maxRequests: number;
  private windowMs: number;

  constructor(limit: number, windowMs: number) {
    this.maxRequests = limit;
    this.windowMs = windowMs;
  }

  async limit(identifier: string) {
    const now = Date.now();
    const requests = this.requests.get(identifier) || [];
    
    // Remove old requests outside the window
    const validRequests = requests.filter(time => now - time < this.windowMs);
    
    if (validRequests.length >= this.maxRequests) {
      return {
        success: false,
        limit: this.maxRequests,
        remaining: 0,
        reset: new Date(validRequests[0] + this.windowMs),
      };
    }
    
    validRequests.push(now);
    this.requests.set(identifier, validRequests);
    
    return {
      success: true,
      limit: this.maxRequests,
      remaining: this.maxRequests - validRequests.length,
      reset: new Date(now + this.windowMs),
    };
  }
}

// Development fallbacks
export const devApiRatelimit = new InMemoryRatelimit(20, 60 * 1000);
export const devAuthRatelimit = new InMemoryRatelimit(5, 5 * 60 * 1000);
export const devGeneralRatelimit = new InMemoryRatelimit(100, 60 * 1000);

// Export helper to get the appropriate rate limiter
export function getRatelimit(type: 'api' | 'auth' | 'general') {
  if (process.env.NODE_ENV === 'production' && !isRedisConfigured) {
    console.warn('⚠️ UPSTASH_REDIS_REST_URL or UPSTASH_REDIS_REST_TOKEN not configured. Rate limiting disabled.');
    return null;
  }

  if (type === 'api') return apiRatelimit || devApiRatelimit;
  if (type === 'auth') return authRatelimit || devAuthRatelimit;
  return generalRatelimit || devGeneralRatelimit;
}
