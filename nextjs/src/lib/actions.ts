'use server';

import { signOut } from "@/lib/auth";

// Secure action for updating own profile
// DEPRECATED: Use client-side logic in @/lib/client-actions.ts
// export async function updateUserProfile(formData: FormData) { ... }

export async function signOutAction() {
    await signOut({ redirectTo: "/" });
}

// NOTE: Data mutation actions (updateAlert, updatePatient) have been moved to @/lib/client-actions.ts
// to support Vercel deployment without Admin SDK keys.
// Server Actions cannot write to Firestore without a Service Account.

