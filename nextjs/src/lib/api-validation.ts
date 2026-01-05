/**
 * API Input Validation Schemas
 * 
 * Centralized Zod schemas for server-side API validation.
 * Use these in API routes to validate incoming requests.
 */

import { z } from 'zod';

// ============================================================================
// USER SCHEMAS
// ============================================================================

export const createUserSchema = z.object({
  email: z.string().email('Invalid email address'),
  name: z.string().min(2, 'Name must be at least 2 characters'),
  role: z.enum(['nurse', 'coordinator', 'admin'], {
    errorMap: () => ({ message: 'Role must be nurse, coordinator, or admin' }),
  }),
  department: z.string().optional(),
  hospitalId: z.string().min(1, 'Hospital ID is required'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

export const updateUserSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters').optional(),
  department: z.string().optional(),
  // Role and hospitalId cannot be changed by user
});

export const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
});

// ============================================================================
// PATIENT SCHEMAS
// ============================================================================

export const createPatientSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  dateOfBirth: z.string().refine((date) => !isNaN(Date.parse(date)), {
    message: 'Invalid date format',
  }),
  gender: z.enum(['male', 'female', 'other'], {
    errorMap: () => ({ message: 'Gender must be male, female, or other' }),
  }),
  phone: z.string().regex(/^\+?[1-9]\d{1,14}$/, 'Invalid phone number'),
  email: z.string().email('Invalid email address').optional(),
  address: z.string().optional(),
  hospitalId: z.string().min(1, 'Hospital ID is required'),
  mrn: z.string().min(1, 'Medical Record Number is required'),
  diagnosis: z.string().min(1, 'Diagnosis is required'),
  admissionDate: z.string().refine((date) => !isNaN(Date.parse(date)), {
    message: 'Invalid date format',
  }),
  dischargeDate: z.string().refine((date) => !isNaN(Date.parse(date)), {
    message: 'Invalid date format',
  }),
  status: z.enum(['active', 'discharged', 'deceased'], {
    errorMap: () => ({ message: 'Invalid status' }),
  }),
  riskLevel: z.enum(['low', 'medium', 'high'], {
    errorMap: () => ({ message: 'Invalid risk level' }),
  }),
  medications: z.array(z.object({
    name: z.string(),
    dosage: z.string(),
    frequency: z.string(),
  })).optional(),
  notes: z.string().optional(),
});

export const updatePatientSchema = createPatientSchema.partial();

// ============================================================================
// ALERT SCHEMAS
// ============================================================================

export const createAlertSchema = z.object({
  patientId: z.string().min(1, 'Patient ID is required'),
  severity: z.enum(['safe', 'warning', 'critical'], {
    errorMap: () => ({ message: 'Invalid severity level' }),
  }),
  type: z.enum(['vital_signs', 'medication', 'appointment', 'other'], {
    errorMap: () => ({ message: 'Invalid alert type' }),
  }),
  message: z.string().min(10, 'Message must be at least 10 characters'),
  recommendation: z.string().optional(),
  hospitalId: z.string().min(1, 'Hospital ID is required'),
});

export const updateAlertSchema = z.object({
  status: z.enum(['pending', 'acknowledged', 'resolved'], {
    errorMap: () => ({ message: 'Invalid status' }),
  }),
  acknowledgedBy: z.string().optional(),
  acknowledgedAt: z.string().optional(),
  resolvedBy: z.string().optional(),
  resolvedAt: z.string().optional(),
  notes: z.string().optional(),
});

// ============================================================================
// NOTIFICATION SCHEMAS
// ============================================================================

export const createNotificationSchema = z.object({
  userId: z.string().min(1, 'User ID is required'),
  title: z.string().min(1, 'Title is required'),
  message: z.string().min(1, 'Message is required'),
  type: z.enum(['info', 'warning', 'error', 'success'], {
    errorMap: () => ({ message: 'Invalid notification type' }),
  }),
  link: z.string().optional(),
});

// ============================================================================
// AUDIT LOG SCHEMAS
// ============================================================================

export const createAuditLogSchema = z.object({
  userId: z.string().min(1, 'User ID is required'),
  action: z.string().min(1, 'Action is required'),
  resource: z.string().min(1, 'Resource is required'),
  resourceId: z.string().min(1, 'Resource ID is required'),
  hospitalId: z.string().min(1, 'Hospital ID is required'),
  details: z.record(z.any()).optional(),
  ipAddress: z.string().optional(),
  userAgent: z.string().optional(),
});

// ============================================================================
// HELPER TYPES
// ============================================================================

export type CreateUserInput = z.infer<typeof createUserSchema>;
export type UpdateUserInput = z.infer<typeof updateUserSchema>;
export type LoginInput = z.infer<typeof loginSchema>;
export type CreatePatientInput = z.infer<typeof createPatientSchema>;
export type UpdatePatientInput = z.infer<typeof updatePatientSchema>;
export type CreateAlertInput = z.infer<typeof createAlertSchema>;
export type UpdateAlertInput = z.infer<typeof updateAlertSchema>;
export type CreateNotificationInput = z.infer<typeof createNotificationSchema>;
export type CreateAuditLogInput = z.infer<typeof createAuditLogSchema>;

// ============================================================================
// VALIDATION HELPER
// ============================================================================

/**
 * Validate request body against a Zod schema
 * Returns validated data or throws with formatted errors
 */
export function validateRequest<T>(
  schema: z.ZodSchema<T>,
  data: unknown
): T {
  try {
    return schema.parse(data);
  } catch (error) {
    if (error instanceof z.ZodError) {
      const formattedErrors = error.errors.map((err) => ({
        field: err.path.join('.'),
        message: err.message,
      }));
      
      throw {
        status: 400,
        message: 'Validation failed',
        errors: formattedErrors,
      };
    }
    throw error;
  }
}

/**
 * Safe validation that returns success/error object
 */
export function safeValidateRequest<T>(
  schema: z.ZodSchema<T>,
  data: unknown
): { success: true; data: T } | { success: false; errors: Array<{ field: string; message: string }> } {
  const result = schema.safeParse(data);
  
  if (result.success) {
    return { success: true, data: result.data };
  }
  
  const formattedErrors = result.error.errors.map((err) => ({
    field: err.path.join('.'),
    message: err.message,
  }));
  
  return { success: false, errors: formattedErrors };
}
