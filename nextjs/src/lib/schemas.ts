import { z } from "zod";

// Define allowed Risk Levels
export const RiskLevelSchema = z.enum(['safe', 'warning', 'critical']);

// Schemas for Medication
export const MedicationSchema = z.object({
    name: z.string().min(1, "Medication name is required"),
    dosage: z.string(),
    frequency: z.string(),
    instructions: z.string().optional().default(""),
});

// Strict Schema for Updating a Patient
// We explicitly exclude 'hospitalId' and 'id' to prevent Mass Assignment/Tenant hopping
export const updatePatientSchema = z.object({
    name: z.string().min(1).optional(),
    preferredLanguage: z.string().optional(),
    diagnosis: z.string().optional(),
    dischargeDate: z.string().optional(),
    contactNumber: z.string().optional(),
    email: z.string().email().optional(),
    dateOfBirth: z.string().optional(),
    medicationPlan: z.array(MedicationSchema).optional(),
    currentStatus: RiskLevelSchema.optional(),
    // Allow updating nested contact preferences
    contact: z.object({
        preferredMethod: z.enum(['call', 'sms', 'email']).optional()
    }).optional(),
    // Allow updating next appointment
    nextAppointment: z.object({
        date: z.string(),
        type: z.string(),
        location: z.string()
    }).optional(),
});

// Strict Schema for Updating an Alert
export const updateAlertSchema = z.object({
    status: z.enum(['active', 'resolved', 'in_progress']).optional(),
    priority: RiskLevelSchema.optional(),
    resolutionNote: z.string().optional(),
});
