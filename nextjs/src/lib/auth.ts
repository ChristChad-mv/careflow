/**
 * NextAuth Configuration for CareFlow Pulse
 * 
 * Healthcare-focused authentication with role-based access control.
 * Integrates with Firebase Authentication.
 */

import NextAuth, { DefaultSession } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { initAdmin } from "@/lib/firebase-admin";
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
          const admin = await initAdmin();

          // Verify the ID token sent from the client
          const decodedToken = await admin.auth().verifyIdToken(token);

          // Extract user details
          const { uid, email, name, picture } = decodedToken;

          // TODO: Fetch additional user details (role, department) from Firestore
          // For now, we'll default to "nurse" if not set in custom claims
          // In a real app, you would read from /users/{uid} here

          // Mock role assignment for demonstration until Firestore user record is created
          // You should set custom claims on the user in Firebase or read from Firestore
          const role = (decodedToken.role as any) || "nurse";
          const hospitalId = (decodedToken.hospitalId as any) || "HOSP001";
          const department = (decodedToken.department as any) || "General";

          return {
            id: uid,
            email: email || "",
            name: name || email?.split("@")[0] || "User",
            image: picture,
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
