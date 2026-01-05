'use server';

import { getAdminDb } from "@/lib/firebase-admin";
import { revalidatePath } from "next/cache";
import { auth, signOut } from "@/lib/auth";

// Secure action for updating own profile
export async function updateUserProfile(formData: FormData) {
    const session = await auth();
    if (!session?.user?.id) return { success: false, error: "Not authenticated" };

    const db = await getAdminDb();

    // Extract data from form
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

export async function updateAlert(alertId: string, data: {
    status?: string;
    priority?: string;
    resolutionNote?: string;
}) {
    if (!alertId) throw new Error("Alert ID is required");

    const db = await getAdminDb();

    // Clean undefined values
    const updateData = JSON.parse(JSON.stringify(data));

    await db.collection("alerts").doc(alertId).update(updateData);

    revalidatePath('/');
    revalidatePath('/alerts');
    revalidatePath(`/alerts/${alertId}`);
    return { success: true };
}

export async function updatePatient(patientId: string, data: any) {
    if (!patientId) throw new Error("Patient ID is required");

    const db = await getAdminDb();

    // Clean text fields like "instructions" that might come from textarea
    if (data.medicationPlan) {
        data.medicationPlan = data.medicationPlan.map((med: any) => ({
            ...med,
            instructions: med.instructions || ""
        }));
    }

    // Clean undefined values
    const updateData = JSON.parse(JSON.stringify(data));

    await db.collection("patients").doc(patientId).update(updateData);

    revalidatePath('/patients');
    revalidatePath(`/patient/${patientId}`);
    return { success: true };
}
