/**
 * Environment Configuration
 * 
 * Centralized configuration management with validation and type safety.
 * This ensures all environment variables are validated at startup.
 */

import { z } from 'zod';

// Define the schema for environment variables
const envSchema = z.object({
  // Node environment
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  
  // Public app configuration
  NEXT_PUBLIC_APP_URL: z.string().url().default('http://localhost:3000'),
  NEXT_PUBLIC_APP_NAME: z.string().default('CareFlow Pulse'),
  
  // API configuration
  NEXT_PUBLIC_API_URL: z.string().url().optional(),
  
  // Feature flags
  NEXT_PUBLIC_ENABLE_AI_AGENT: z.string().default('false').transform(val => val === 'true'),
  NEXT_PUBLIC_ENABLE_SMS_ALERTS: z.string().default('false').transform(val => val === 'true'),
  NEXT_PUBLIC_ENABLE_AUDIT_LOGS: z.string().default('true').transform(val => val === 'true'),
  
  // Google Cloud (optional for development)
  GOOGLE_CLOUD_PROJECT: z.string().optional(),
  GOOGLE_CLOUD_LOCATION: z.string().optional(),
  REASONING_ENGINE_ID: z.string().optional(),
  AGENT_ENGINE_ENDPOINT: z.string().url().optional(),
  ADK_APP_NAME: z.string().optional(),
});

// Parse and validate environment variables
function validateEnv() {
  const parsed = envSchema.safeParse({
    NODE_ENV: process.env.NODE_ENV,
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
    NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME,
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_ENABLE_AI_AGENT: process.env.NEXT_PUBLIC_ENABLE_AI_AGENT,
    NEXT_PUBLIC_ENABLE_SMS_ALERTS: process.env.NEXT_PUBLIC_ENABLE_SMS_ALERTS,
    NEXT_PUBLIC_ENABLE_AUDIT_LOGS: process.env.NEXT_PUBLIC_ENABLE_AUDIT_LOGS,
    GOOGLE_CLOUD_PROJECT: process.env.GOOGLE_CLOUD_PROJECT,
    GOOGLE_CLOUD_LOCATION: process.env.GOOGLE_CLOUD_LOCATION,
    REASONING_ENGINE_ID: process.env.REASONING_ENGINE_ID,
    AGENT_ENGINE_ENDPOINT: process.env.AGENT_ENGINE_ENDPOINT,
    ADK_APP_NAME: process.env.ADK_APP_NAME,
  });

  if (!parsed.success) {
    console.error('❌ Invalid environment variables:', parsed.error.flatten().fieldErrors);
    throw new Error('Invalid environment variables');
  }

  return parsed.data;
}

// Export validated environment variables
export const env = validateEnv();

// Type-safe environment access
export const config = {
  // App configuration
  app: {
    name: env.NEXT_PUBLIC_APP_NAME,
    url: env.NEXT_PUBLIC_APP_URL,
    env: env.NODE_ENV,
  },
  
  // API configuration
  api: {
    url: env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  
  // Feature flags
  features: {
    aiAgent: env.NEXT_PUBLIC_ENABLE_AI_AGENT,
    smsAlerts: env.NEXT_PUBLIC_ENABLE_SMS_ALERTS,
    auditLogs: env.NEXT_PUBLIC_ENABLE_AUDIT_LOGS,
  },
  
  // Google Cloud configuration
  googleCloud: {
    project: env.GOOGLE_CLOUD_PROJECT,
    location: env.GOOGLE_CLOUD_LOCATION,
    reasoningEngineId: env.REASONING_ENGINE_ID,
    agentEngineEndpoint: env.AGENT_ENGINE_ENDPOINT,
    adkAppName: env.ADK_APP_NAME,
  },
  
  // Helper functions
  isDevelopment: env.NODE_ENV === 'development',
  isProduction: env.NODE_ENV === 'production',
  isTest: env.NODE_ENV === 'test',
} as const;

// Validate environment on module load
if (typeof window === 'undefined') {
  // Server-side only - log configuration status

}
