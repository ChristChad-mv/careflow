import { getAdminDb } from "@/lib/firebase-admin";

export interface AuditLogEntry {
    action: 'READ' | 'WRITE' | 'DELETE' | 'LOGIN' | 'LOGOUT';
    resourceType: 'patient' | 'alert' | 'user' | 'system';
    resourceId: string;
    details?: string;
    hospitalId: string;
    actor: {
        userId: string;
        ip?: string;
        role?: string; // e.g. 'nurse', 'doctor'
    };
    metadata?: Record<string, any>;
}

export class AuditService {
    private static COLLECTION_NAME = 'audit_logs';

    /**
     * Logs an action for HIPAA compliance.
     * This creates an immutable record in the audit_logs collection.
     */
    static async log(entry: AuditLogEntry) {
        const db = await getAdminDb();

        try {
            await db.collection(this.COLLECTION_NAME).add({
                ...entry,
                timestamp: new Date().toISOString(), // Use server timestamp ideally, but ISO string conforms to our schema
                // Add a server timestamp field if needed for strict ordering
                _serverTimestamp: new Date(),
            });
            // console.log(`[AUDIT] Logged ${entry.action} on ${entry.resourceType}/${entry.resourceId}`);
        } catch (error) {
            // Critical: Failure to audit is a security incident.
            // In a real production system, this should trigger a paging alert.
            console.error(`[CRITICAL AUDIT FAILURE] Failed to log audit entry details:`, entry, error);
            // We do NOT throw here to prevent breaking the user flow, but strictly we should.
            // For this app, logging to stderr is the fallback.
        }
    }
}
