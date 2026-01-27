import { db } from "@/lib/firebase";
import { doc, updateDoc, collection, addDoc, getDoc } from "firebase/firestore";
import { updateAlertSchema, updatePatientSchema } from "@/lib/schemas";
import { UserContext } from "@/lib/db";

// Client-side Audit Logging
async function logAudit(
    action: 'WRITE' | 'READ' | 'DELETE',
    resourceType: 'patient' | 'alert' | 'user',
    resourceId: string,
    details: string,
    user: UserContext
) {
    try {
        await addDoc(collection(db, "audit_logs"), {
            action,
            resourceType,
            resourceId,
            hospitalId: user.hospitalId,
            actor: {
                userId: user.email, // Best identifier we have on client context usually
                role: user.role
            },
            details,
            timestamp: new Date().toISOString()
        });
    } catch (e) {
        console.error("Failed to write audit log:", e);
        // Don't block the main action for audit failure on client
    }
}

export async function updateAlertClient(alertId: string, data: unknown, user: UserContext) {
    if (!user || !user.hospitalId) throw new Error("Unauthorized");

    // 1. Validation
    const parsed = updateAlertSchema.safeParse(data);
    if (!parsed.success) {
        throw new Error(`Invalid data: ${parsed.error.issues.map(i => i.message).join(", ")}`);
    }

    // 2. Tenant Check & Existence
    const alertRef = doc(db, "alerts", alertId);
    const alertSnap = await getDoc(alertRef);

    if (!alertSnap.exists()) throw new Error("Alert not found");
    if (alertSnap.data()?.hospitalId !== user.hospitalId) throw new Error("Unauthorized: Tenant Mismatch");

    // 3. Update
    await updateDoc(alertRef, parsed.data);

    // 4. Audit
    await logAudit('WRITE', 'alert', alertId, `Updated status/priority`, user);

    return { success: true };
}

export async function updatePatientClient(patientId: string, data: unknown, user: UserContext) {
    if (!user || !user.hospitalId) throw new Error("Unauthorized");

    // 1. Validation
    const parsed = updatePatientSchema.safeParse(data);
    if (!parsed.success) {
        throw new Error(`Validation Error: ${parsed.error.issues.map(i => i.message).join(", ")}`);
    }

    // 2. Tenant Check
    const patientRef = doc(db, "patients", patientId);
    const patientSnap = await getDoc(patientRef);

    if (!patientSnap.exists()) throw new Error("Patient not found");
    if (patientSnap.data()?.hospitalId !== user.hospitalId) throw new Error("Unauthorized: Tenant Mismatch");

    // 3. Update
    await updateDoc(patientRef, parsed.data);

    // 4. Audit
    await logAudit('WRITE', 'patient', patientId, `Updated fields: ${Object.keys(parsed.data).join(', ')}`, user);

    return { success: true };
}

export async function createPatientClient(data: any, user: UserContext) {
    if (!user || !user.hospitalId) throw new Error("Unauthorized");

    const patientData = {
        ...data,
        hospitalId: user.hospitalId,
        createdAt: new Date().toISOString(),
        currentStatus: data.currentStatus || 'safe',
        medicationPlan: data.medicationPlan || [],
    };

    // Basic validation
    if (!patientData.name || !patientData.contactNumber) {
        throw new Error("Name and Contact Number are required");
    }

    const docRef = await addDoc(collection(db, "patients"), patientData);

    await logAudit('WRITE', 'patient', docRef.id, `Created patient: ${patientData.name}`, user);

    return { success: true, id: docRef.id };
}

export async function updateUserProfileClient(userId: string, data: { name: string; hospitalId: string }, user: UserContext) {
    if (!userId || !user) throw new Error("Unauthorized");

    const userRef = doc(db, "users", userId);

    // We update name only (hospitalId is immutable for users)
    await updateDoc(userRef, {
        name: data.name
    });

    await logAudit('WRITE', 'user', userId, `Updated profile: ${data.name}`, user);

    return { success: true };
}
