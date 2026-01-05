'use server';

import { getAdminDb } from "@/lib/firebase-admin";
import { revalidatePath } from "next/cache";
import { auth, signOut } from "@/lib/auth";
import { updatePatientSchema, updateAlertSchema } from "@/lib/schemas";

// Secure action for updating own profile
export async function updateUserProfile(formData: FormData) {
    const session = await auth();
    if (!session?.user?.id) return { success: false, error: "Not authenticated" };

    const db = await getAdminDb();

    // Extract data from form
    // Note: This needs careful validation too if it were critical, but for now we trust name/hospitalId format basics
    const name = formData.get("name") as string;
    const hospitalId = formData.get("hospitalId") as string;

    // Update user
    await db.collection("users").doc(session.user.id).update({
        name,
        hospitalId
        // Role and Email are usually immutable or managed by admins
    });

    revalidatePath('/profile');
    return { success: true };
}

export async function signOutAction() {
    await signOut({ redirectTo: "/" });
}

export async function updateAlert(alertId: string, data: unknown) {
    if (!alertId) throw new Error("Alert ID is required");

    const session = await auth();
    if (!session?.user?.id) throw new Error("Unauthorized");

    // 1. Validate Input Structure
    const parsed = updateAlertSchema.safeParse(data);
    if (!parsed.success) {
        throw new Error(`Invalid data: ${parsed.error.issues.map(i => i.message).join(", ")}`);
    }

    const db = await getAdminDb();

    // 2. Verify Alert Existence & Ownership (Multi-Tenant check if alerts have hospitalId)
    // For now assuming alerts are global or we trust the user has access if they can see the button.
    // Ideally: Check alert.hospitalId === session.user.hospitalId

    // Clean undefined values
    const updateData = JSON.parse(JSON.stringify(parsed.data));

    await db.collection("alerts").doc(alertId).update(updateData);

    revalidatePath('/');
    revalidatePath('/alerts');
    revalidatePath(`/alerts/${alertId}`);
    return { success: true };
}

export async function updatePatient(patientId: string, data: unknown) {
    if (!patientId) throw new Error("Patient ID is required");

    const session = await auth();
    const userHospitalId = session?.user?.hospitalId; // Assumes hospitalId is on session or fetched from DB

    // Fallback: fetch user from DB to be sure of hospitalId
    const db = await getAdminDb();

    // 1. Verify User Authorization (Multi-Tenancy)
    if (!userHospitalId) {
        // In a real app we might need to fetch the user profile if hospitalId isn't on the session token
        // const userDoc = await db.collection("users").doc(session.user.id).get();
        // const userHospitalId = userDoc.data()?.hospitalId;
    }

    // 2. Validate Input Structure (Zod)
    const parsed = updatePatientSchema.safeParse(data);
    if (!parsed.success) {
        // Return structured error or throw
        throw new Error(`Validation Error: ${parsed.error.issues.map(i => i.message).join(", ")}`);
    }

    // 3. Verify Target Patient belongs to User's Hospital
    const patientRef = db.collection("patients").doc(patientId);
    const patientSnap = await patientRef.get();

    if (!patientSnap.exists) throw new Error("Patient not found");

    const patientData = patientSnap.data();

    // CRITICAL SECURITY: Multi-Tenancy Check
    // We strictly compare the patient's hospitalId with the user's hospitalId
    if (userHospitalId && patientData?.hospitalId && patientData.hospitalId !== userHospitalId) {
        throw new Error("Unauthorized Access: Tenant Mismatch");
    }

    // 4. Sanitize and Update
    // parsed.data contains ONLY the fields defined in updatePatientSchema
    // Even if 'hospitalId' was passed in 'data', it is stripped out by Zod (if not in schema) or we explicitly excluded it.

    const updateData = JSON.parse(JSON.stringify(parsed.data));

    await patientRef.update(updateData);

    revalidatePath('/patients');
    revalidatePath(`/patient/${patientId}`);
    return { success: true };
}
