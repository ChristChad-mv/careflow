/**
 * Input Validation Schemas for CareFlow Pulse
 * 
 * These schemas ensure all user inputs are validated before processing,
 * protecting against injection attacks and malformed data.
 */

import { z } from 'zod';

// Patient ID validation - Must match format P001, P002, etc.
export const patientIdSchema = z.string()
  .regex(/^P\d{3}$/, 'Patient ID must be in format P001, P002, etc.')
  .trim();

// Alert ID validation - Must match format A001, A002, etc.
export const alertIdSchema = z.string()
  .regex(/^A\d{3}$/, 'Alert ID must be in format A001, A002, etc.')
  .trim();

// Interaction ID validation - Must match format I001, I002, etc.
export const interactionIdSchema = z.string()
  .regex(/^I\d{3}$/, 'Interaction ID must be in format I001, I002, etc.')
  .trim();

// Phone number validation - US format
export const phoneNumberSchema = z.string()
  .regex(/^\+1 \(\d{3}\) \d{3}-\d{4}$/, 'Phone number must be in format +1 (555) 123-4567')
  .trim();

// Email validation
export const emailSchema = z.string()
  .email('Invalid email address')
  .toLowerCase()
  .trim();

// Date validation - ISO format
export const dateSchema = z.string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in format YYYY-MM-DD');

// Status validation
export const statusSchema = z.enum(['safe', 'warning', 'critical']);

// Risk level validation
export const riskLevelSchema = z.enum(['safe', 'warning', 'critical']);

// Search query validation (prevent XSS)
export const searchQuerySchema = z.string()
  .max(100, 'Search query too long')
  .regex(/^[a-zA-Z0-9\s\-_]+$/, 'Search query contains invalid characters')
  .trim();

// Pagination parameters
export const paginationSchema = z.object({
  page: z.number().int().positive().default(1),
  limit: z.number().int().positive().max(100).default(10),
});

// Sort parameters
export const sortSchema = z.object({
  field: z.string().max(50),
  order: z.enum(['asc', 'desc']).default('asc'),
});

// Helper function to validate and sanitize patient ID
export function validatePatientId(id: unknown): string {
  const result = patientIdSchema.safeParse(id);
  if (!result.success) {
    throw new Error(`Invalid patient ID: ${result.error.message}`);
  }
  return result.data;
}

// Helper function to validate and sanitize alert ID
export function validateAlertId(id: unknown): string {
  const result = alertIdSchema.safeParse(id);
  if (!result.success) {
    throw new Error(`Invalid alert ID: ${result.error.message}`);
  }
  return result.data;
}

// Helper function to validate search query
export function validateSearchQuery(query: unknown): string {
  const result = searchQuerySchema.safeParse(query);
  if (!result.success) {
    throw new Error(`Invalid search query: ${result.error.message}`);
  }
  return result.data;
}

// Type exports for use in components
export type ValidatedPatientId = z.infer<typeof patientIdSchema>;
export type ValidatedAlertId = z.infer<typeof alertIdSchema>;
export type ValidatedStatus = z.infer<typeof statusSchema>;
export type ValidatedRiskLevel = z.infer<typeof riskLevelSchema>;
export type ValidatedPagination = z.infer<typeof paginationSchema>;
export type ValidatedSort = z.infer<typeof sortSchema>;
