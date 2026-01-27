/**
 * NextAuth Configuration for CareFlow Pulse
 * 
 * Healthcare-focused authentication with role-based access control.
 * Integrates with Firebase Authentication via REST API and Firestore Client SDK.
 */

import NextAuth, { DefaultSession } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { authConfig } from "./auth.config";


// Extend the built-in session type
declare module "next-auth" {
  interface Session extends DefaultSession {
    user: {
      id: string;
      email: string;
      name: string;
      role: "nurse" | "coordinator" | "admin";
      department?: string;
      hospitalId?: string;
    } & DefaultSession["user"];
  }

  interface User {
    id: string;
    email: string;
    name: string;
    role: "nurse" | "coordinator" | "admin";
    department?: string;
    hospitalId?: string;
  }
}

export const { handlers, signIn, signOut, auth } = NextAuth({
  ...authConfig,
  providers: [
    CredentialsProvider({
      name: "Firebase",
      credentials: {
        token: { label: "ID Token", type: "text" },
      },
      async authorize(credentials) {
        try {
          if (!credentials?.token) {
            console.error("No token provided");
            return null;
          }

          const token = credentials.token as string;

          // 1. Verify ID Token using Google Identity Toolkit API (Stateless/Keyless)
          // This avoids the need for Admin SDK Service Account Keys on Vercel
          const apiKey = process.env.NEXT_PUBLIC_FIREBASE_API_KEY;
          const verifyUrl = `https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=${apiKey}`;

          const response = await fetch(verifyUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idToken: token })
          });

          const data = await response.json();

          if (!response.ok || !data.users || data.users.length === 0) {
            console.error("Token verification failed:", data.error || "Unknown error");
            return null;
          }

          const firebaseUser = data.users[0];
          const uid = firebaseUser.localId;
          const email = firebaseUser.email;

          // 2. Fetch User Details from Firestore (using access token or just public read if allowed, 
          // or strictly relying on the fact that we are the server environment with client SDK)
          // Note: On Vercel, the Client SDK in 'db' might fall back to "Guest" mode or similar 
          // if we don't pass the ID token to it, OR it works if rules allow.
          // Ideally, we should use the ID token to auth the DB connection too, but for now 
          // we assume the DB is initialized in a way that allows this read, or we trust the claim.

          // Actually, we should fetch from Firestore to be secure about Role/HospitalId.
          let role: "nurse" | "coordinator" | "admin" = "nurse";
          let hospitalId = "HOSP001";
          let name = firebaseUser.displayName || email?.split("@")[0] || "User";
          let department = "General";

          try {
            // Fetch user profile from Firestore REST API to ensure we use the user's auth context
            const projectId = process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;
            const firestoreUrl = `https://firestore.googleapis.com/v1/projects/${projectId}/databases/(default)/documents/users/${uid}`;

            const profileResponse = await fetch(firestoreUrl, {
              headers: { 'Authorization': `Bearer ${token}` }
            });

            if (profileResponse.ok) {
              const profileData = await profileResponse.json();
              // Firestore REST API returns fields in a specific format: { fields: { role: { stringValue: "..." } } }
              // We need a helper or manual extraction.
              const fields = profileData.fields;
              if (fields) {
                if (fields.role?.stringValue) role = fields.role.stringValue as any;
                if (fields.hospitalId?.stringValue) hospitalId = fields.hospitalId.stringValue;
                if (fields.name?.stringValue) name = fields.name.stringValue;
                if (fields.department?.stringValue) department = fields.department.stringValue;
              }
            } else {
              console.warn(`Failed to fetch profile via REST: ${profileResponse.status} ${profileResponse.statusText}`);
              // Fallback intended (default values)
            }
          } catch (dbError) {
            console.error("Error fetching user profile from Firestore REST:", dbError);
          }

          return {
            id: uid,
            email: email || "",
            name: name,
            image: firebaseUser.photoUrl,
            role: role,
            department: department,
            hospitalId: hospitalId,
          };

        } catch (error) {
          console.error("Firebase Authentication error:", error);
          return null;
        }
      },
    }),
  ],
});
