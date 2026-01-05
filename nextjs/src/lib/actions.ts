"use server";

import { initAdmin } from "@/lib/firebase-admin";
import { revalidatePath } from "next/cache";
import { auth } from "@/lib/auth";

export async function updateUser(formData: FormData) {
    const session = await auth();
    if (!session?.user?.email) {
        throw new Error("Not authenticated");
    }

    const name = formData.get("name") as string;
    const hospitalId = formData.get("hospitalId") as string;
    // Role is usually managed by admins, so we might skip it or make it read-only in UI

    if (!name || !hospitalId) {
        throw new Error("Missing required fields");
    }

    const admin = await initAdmin();

    // We need the user's UID. 
    // Since we don't have the UID in the session object by default in NextAuth v5 unless we put it there,
    // we might need to look up the user by email or ensure UID is in session.
    // In auth.ts, we are putting 'sub' (uid) into token, and token into session.user.id?
    // Let's check auth.ts. 
    // If session.user.id is available, we use it.

    // Assuming session.user.id is the UID.
    // If not, we can look up by email.
    let uid = session.user.id;

    if (!uid) {
        const userRecord = await admin.auth().getUserByEmail(session.user.email);
        uid = userRecord.uid;
    }

    try {
        // Update Firestore User Document
        await admin.firestore().collection("users").doc(uid).update({
            name,
            hospitalId,
            updatedAt: new Date(),
        });

        // Update Firebase Auth Profile (DisplayName)
        await admin.auth().updateUser(uid, {
            displayName: name,
        });

        revalidatePath("/profile");
        return { success: true };
    } catch (error) {
        console.error("Error updating profile:", error);
        return { success: false, error: "Failed to update profile" };
    }
}
